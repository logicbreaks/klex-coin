"""Node: datadir, chain persistence, mempool, block submission, full verify."""

import json
import os

from . import chain, config, crypto, genesis, miner as miner_mod, tx as tx_mod

CHAIN_FILE = "chain.json"
STATE_FILE = "state.json"
MEMPOOL_FILE = "mempool.json"


def default_datadir() -> str:
    return os.environ.get("KLEX_HOME") or os.path.expanduser("~/.klex")


def atomic_write_json(path: str, obj) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def read_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path} is corrupted ({exc}); restore from backup") from exc


class Node:
    def __init__(self, datadir: str):
        self.datadir = datadir
        self.chain_path = os.path.join(datadir, CHAIN_FILE)
        self.state_path = os.path.join(datadir, STATE_FILE)
        self.mempool_path = os.path.join(datadir, MEMPOOL_FILE)
        self.blocks = read_json(self.chain_path, [])
        self.state = read_json(self.state_path, None)
        self.mempool = read_json(self.mempool_path, [])
        if self.blocks and self.state is None:
            raise RuntimeError("chain exists but state file missing; run klex verify")

    @property
    def initialized(self) -> bool:
        return bool(self.blocks)

    def init(self) -> dict:
        if self.initialized:
            raise ValueError("node already initialized")
        genesis_block = genesis.build_genesis()
        chain.validate_genesis(genesis_block)
        self.blocks = [genesis_block]
        self.state = chain.initial_state()
        self.mempool = []
        self.persist()
        return genesis_block

    def persist(self) -> None:
        os.makedirs(self.datadir, exist_ok=True)
        atomic_write_json(self.chain_path, self.blocks)
        atomic_write_json(self.state_path, self.state)
        atomic_write_json(self.mempool_path, self.mempool)

    def head(self) -> dict:
        return self.blocks[-1]

    def next_reward(self) -> int:
        return chain.block_reward(self.head()["index"] + 1)

    def add_block(self, block: dict) -> dict:
        new_state = chain.validate_block(block, self.blocks, self.state)
        self.blocks.append(block)
        self.state = new_state
        included = {tx_mod.tx_hash(t) for t in block["txs"][1:]}
        self.mempool = [t for t in self.mempool if tx_mod.tx_hash(t) not in included]
        self.persist()
        return block

    def projected_state(self, sender: str | None = None) -> tuple[dict, dict]:
        """Chain state plus all pending mempool txs applied (optionally
        filtered to one sender). This is what new txs are validated against,
        so a sender can queue several transfers."""
        balances = dict(self.state["balances"])
        nonces = dict(self.state["nonces"])
        pending = [t for t in self.mempool if sender is None or t["from"] == sender]
        for t in sorted(pending, key=lambda x: x["nonce"]):
            tx_mod.validate(t, balances, nonces)
            tx_mod.apply(t, balances, nonces)
        return balances, nonces

    def next_nonce(self, address: str) -> int:
        balances, nonces = self.projected_state(address)
        return nonces.get(address, 0) + 1

    def submit_transfer(self, signed_tx: dict) -> str:
        h = tx_mod.tx_hash(signed_tx)
        if any(tx_mod.tx_hash(t) == h for t in self.mempool):
            raise ValueError("duplicate transaction already in mempool")
        balances, nonces = self.projected_state(signed_tx["from"])
        tx_mod.validate(signed_tx, balances, nonces)
        if len(self.mempool) >= config.MEMPOOL_CAP:
            raise ValueError("mempool full")
        self.mempool.append(signed_tx)
        atomic_write_json(self.mempool_path, self.mempool)
        return h

    def mine_block(self, miner_addr: str, max_txs: int | None = None) -> dict:
        if not crypto.address_is_valid(miner_addr):
            raise ValueError("invalid miner address")
        limit = (max_txs or config.MAX_TXS_PER_BLOCK) - 1
        balances, nonces = dict(self.state["balances"]), dict(self.state["nonces"])
        by_sender: dict = {}
        for t in self.mempool:
            by_sender.setdefault(t["from"], []).append(t)
        for lst in by_sender.values():
            lst.sort(key=lambda t: t["nonce"])
        cursors = {s: 0 for s in by_sender}
        selected, stale = [], []
        while len(selected) < limit:
            candidates = []
            for s, lst in by_sender.items():
                i = cursors[s]
                while i < len(lst):
                    t = lst[i]
                    try:
                        tx_mod.validate(t, balances, nonces)
                        candidates.append((t, s, i))
                        break
                    except ValueError:
                        stale.append(t)
                        i += 1
                cursors[s] = i
            if not candidates:
                break
            t, s, i = max(candidates, key=lambda c: c[0].get("fee", 0))
            tx_mod.apply(t, balances, nonces)
            selected.append(t)
            cursors[s] = i + 1
        if stale:
            stale_hashes = {tx_mod.tx_hash(t) for t in stale}
            self.mempool = [t for t in self.mempool if tx_mod.tx_hash(t) not in stale_hashes]
            atomic_write_json(self.mempool_path, self.mempool)
        block = chain.build_block(self.blocks, self.state, selected, miner_addr)
        block, elapsed = miner_mod.solve(block)
        self.add_block(block)
        return block

    def verify(self) -> dict:
        report = {"blocks": len(self.blocks), "errors": []}
        state = chain.initial_state()
        try:
            chain.validate_genesis(self.blocks[0])
        except Exception as exc:
            report["errors"].append(f"genesis: {exc}")
            report["ok"] = False
            return report
        for i in range(1, len(self.blocks)):
            try:
                state = chain.validate_block(self.blocks[i], self.blocks[:i], state)
            except Exception as exc:
                report["errors"].append(f"block {i}: {exc}")
                break
        report["ok"] = not report["errors"]
        report["verified_supply"] = state["supply"]
        stored = self.state
        if report["ok"] and stored:
            if stored.get("height") != state["height"]:
                report["errors"].append(f"stored height {stored.get('height')} != recomputed {state['height']}")
            if stored.get("balances") != state["balances"]:
                report["errors"].append("stored balances diverge from recomputed state")
            if stored.get("supply") != state["supply"]:
                report["errors"].append("stored supply diverges from recomputed supply")
            report["ok"] = not report["errors"]
        report["state"] = state
        return report

    def balance(self, address: str) -> int:
        return self.state["balances"].get(address, 0) if self.state else 0

    def info(self) -> dict:
        if not self.initialized:
            return {"initialized": False}
        head = self.head()
        return {
            "initialized": True,
            "height": self.state["height"],
            "difficulty": self.state["difficulty"],
            "supply": self.state["supply"],
            "reward": chain.block_reward(self.head()["index"] + 1),
            "genesis_hash": self.blocks[0]["hash"],
            "mempool": len(self.mempool),
            "block_time": config.BLOCK_TIME,
            "max_supply": config.MAX_SUPPLY,
        }

    def address_history(self, address: str) -> list:
        found = []
        for block in self.blocks:
            for t in block["txs"]:
                involved = t.get("from") == address or t.get("to") == address
                if t.get("type") == "coinbase" and t.get("to") == address:
                    involved = True
                if involved:
                    found.append({"height": block["index"], "tx_hash": tx_mod.tx_hash(t), "tx": t})
        return found