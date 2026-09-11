"""KLEX command line interface.

Commands: init, info, wallet, balance, send, mine, verify, explore, serve, sync, paper.
"""

import argparse
import getpass
import os
import sys
import time

from . import __version__, chain, config, crypto, explorer, node as node_mod, paper, tx as tx_mod, wallet as wallet_mod

WALLETS_DIR = "wallets"
WALLET_FILE = "wallet.json"


def wallet_path(datadir: str) -> str:
    return os.path.join(datadir, WALLETS_DIR, WALLET_FILE)


def require_wallet_file(datadir: str) -> dict:
    path = wallet_path(datadir)
    if not os.path.exists(path):
        print("no wallet found — run: klex wallet new", file=sys.stderr)
        raise SystemExit(1)
    return wallet_mod.load_wallet(path)


def require_chain(datadir: str) -> node_mod.Node:
    n = node_mod.Node(datadir)
    if not n.initialized:
        print("chain not initialized — run: klex init", file=sys.stderr)
        raise SystemExit(1)
    return n


def cmd_init(args) -> None:
    n = node_mod.Node(args.datadir)
    genesis = n.init()
    print("KLEX node initialized.")
    print(f"genesis hash : {genesis['hash']}")
    print(f"chain id     : {genesis['hash'][:16]}")
    print("genesis says :")
    print(f"  \"{config.GENESIS_MESSAGE}\"")
    print("allocation   : zero coins. Fair launch confirmed.")


def cmd_info(args) -> None:
    n = node_mod.Node(args.datadir)
    if not n.initialized:
        print("not initialized — run: klex init")
        return
    for k, v in n.info().items():
        print(f"{k:14} {v}")


def cmd_wallet(args) -> None:
    if args.action == "new":
        path = wallet_path(args.datadir)
        if os.path.exists(path) and not args.force:
            print("wallet exists (use --force to replace); refusing to overwrite keys.")
            raise SystemExit(1)
        wallet = wallet_mod.create_wallet_file(path)
        print("wallet created (keystore encrypted, file mode 600)")
        print(f"address : {wallet['address']}")
        print("IMPORTANT: back up this file and your passphrase. No passphrase, no coins.")
    else:
        print(require_wallet_file(args.datadir)["address"])


def cmd_balance(args) -> None:
    n = require_chain(args.datadir)
    address = args.address
    if address is None:
        address = require_wallet_file(args.datadir)["address"]
    if not crypto.address_is_valid(address):
        print("invalid address", file=sys.stderr)
        raise SystemExit(1)
    print(f"{n.balance(address)} KLEX  ({address})")


def cmd_send(args) -> None:
    n = require_chain(args.datadir)
    wallet = require_wallet_file(args.datadir)
    passphrase = getpass.getpass("keystore passphrase: ")
    secret = wallet_mod.secret_key_from_wallet(wallet, passphrase)
    pubkey = crypto.decode_b64(wallet["pubkey_b64"])
    sender = wallet["address"]
    pending_nonces = [t["nonce"] for t in n.mempool if t["from"] == sender]
    if pending_nonces:
        print("a transaction is already pending; wait for the next block to mine it", file=sys.stderr)
        raise SystemExit(1)
    nonce = n.state["nonces"].get(sender, 0) + 1
    tx = tx_mod.build_transfer(sender, args.to, args.amount, nonce, fee=args.fee, memo=args.memo or "")
    signed = tx_mod.sign_transfer(tx, crypto.decode_b64(wallet["pubkey_b64"]), secret)
    tx_mod.validate(signed, n.state["balances"], n.state["nonces"])
    h = n.submit_transfer(signed)
    print(f"tx submitted  {h}")
    print(f"{args.amount} KLEX → {args.to}" + (f"  memo: {args.memo}" if args.memo else ""))
    print("it will be included when the next block is mined")


def cmd_mine(args) -> None:
    n = require_chain(args.datadir)
    miner_addr = require_wallet_file(args.datadir)["address"]
    mined = 0
    try:
        while True:
            pending = len(n.mempool)
            started = time.time()
            block = n.mine_block(miner_addr)
            elapsed = time.time() - started
            reward = block["txs"][0]["amount"]
            mined += 1
            print(
                f"block #{block['index']} found in {elapsed:.1f}s · +{reward} KLEX → "
                f"{miner_addr[:14]}… · difficulty {block['difficulty']} · txs {len(block['txs']) - 1} (mempool {pending})"
            )
            if args.blocks and mined >= args.blocks:
                break
    except KeyboardInterrupt:
        print()
    finally:
        print(f"done. mined {mined} block(s). run `klex verify` to check integrity.")


def cmd_verify(args) -> None:
    n = node_mod.Node(args.datadir)
    if not n.initialized:
        print("not initialized", file=sys.stderr)
        raise SystemExit(1)
    report = n.verify()
    if report["ok"]:
        print(f"chain valid · {report['blocks']} blocks · supply {report['verified_supply']} KLEX")
        print(f"genesis hash : {crypto.EXPECTED_GENESIS_HASH}")
        print(f"message      : \"{config.GENESIS_MESSAGE}\"")
    else:
        for err in report["errors"]:
            print(f"INVALID · {err}", file=sys.stderr)
        raise SystemExit(1)


def cmd_explore(args) -> None:
    n = require_chain(args.datadir)
    explorer.serve(n, host="127.0.0.1", port=args.port)


def cmd_serve(args) -> None:
    n = require_chain(args.datadir)
    from . import net

    net.serve(n, host="127.0.0.1", port=args.port)


def cmd_sync(args) -> None:
    n = node_mod.Node(args.datadir)
    if not n.initialized:
        print("not initialized — run: klex init first", file=sys.stderr)
        raise SystemExit(1)
    from . import net

    net.sync(n, args.node)


def cmd_paper(args) -> None:
    n = node_mod.Node(args.datadir)
    if not n.initialized:
        print("not initialized — run: klex init", file=sys.stderr)
        raise SystemExit(1)
    address = args.address
    if address is None:
        address = require_wallet_file(args.datadir)["address"]
    out = args.out or os.path.join(args.datadir, "certificate.html")
    paper.generate_certificate(n, address, out)
    print(f"certificate written: {out}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="klex", description="KLEX node, wallet, miner and explorer")
    p.add_argument("--datadir", default=None, help="node data directory (default ~/.klex)")
    p.add_argument("--version", action="version", version=f"klex {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="initialize node with the genesis block")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("info", help="show node status")
    s.set_defaults(func=cmd_info)

    s = sub.add_parser("wallet", help="create or show the wallet")
    s.add_argument("action", choices=["new", "show"], nargs="?", default="show")
    s.add_argument("--force", action="store_true", help="overwrite existing wallet")
    s.set_defaults(func=cmd_wallet)

    s = sub.add_parser("balance", help="balance of an address (default: your wallet)")
    s.add_argument("address", nargs="?", default=None)
    s.set_defaults(func=cmd_balance)

    s = sub.add_parser("send", help="sign and submit a transfer")
    s.add_argument("to", help="recipient KLEX address")
    s.add_argument("amount", type=int, help="whole KLEX to send")
    s.add_argument("--fee", type=int, default=0)
    s.add_argument("--memo", default="")
    s.set_defaults(func=cmd_send)

    s = sub.add_parser("mine", help="mine blocks (Ctrl-C to stop)")
    s.add_argument("--blocks", type=int, default=0, help="stop after N blocks (0 = forever)")
    s.set_defaults(func=cmd_mine)

    s = sub.add_parser("verify", help="re-validate the entire chain from genesis")
    s.set_defaults(func=cmd_verify)

    s = sub.add_parser("explore", help="run the local explorer (localhost only)")
    s.add_argument("--port", type=int, default=config.EXPLORER_PORT)
    s.set_defaults(func=cmd_explore)

    s = sub.add_parser("serve", help="serve blocks to peers")
    s.add_argument("--port", type=int, default=config.P2P_PORT)
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("sync", help="sync blocks from a peer host:port")
    s.add_argument("node")
    s.set_defaults(func=cmd_sync)

    s = sub.add_parser("paper", help="generate the printable genesis certificate")
    s.add_argument("--address", default=None)
    s.add_argument("--out", default=None)
    s.set_defaults(func=cmd_paper)
    return p


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.datadir = args.datadir or node_mod.default_datadir()
    try:
        args.func(args)
    except SystemExit:
        raise
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()