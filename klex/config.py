"""Chain constants and genesis identity. Values here are consensus-critical."""

import calendar
import datetime

NAME = "KLEX"
VERSION = "1.0.0"

MAX_SUPPLY = 21_000_000
BLOCK_REWARD = 50
HALVING_INTERVAL = 210_000
BLOCK_TIME = 60
RETARGET_INTERVAL = 10
MIN_DIFFICULTY = 3
MAX_DIFFICULTY = 8
MAX_TXS_PER_BLOCK = 64
MEMPOOL_CAP = 500
MAX_MEMO_LEN = 96
MIN_FEE = 0
MAX_FEE = 1_000

GENESIS_MESSAGE = (
    "KLEX · GENESIS · Built overnight with zero budget and full intent, "
    "for the one who taught me the future is built, not bought. "
    "Fair launch. No premine. Value starts at zero — like everything great. — K"
)

_G = datetime.datetime(2026, 9, 11, 0, 0, 0, tzinfo=datetime.timezone.utc)
GENESIS_TIMESTAMP = int(_G.timestamp())
GENESIS_DIFFICULTY = 5
GENESIS_NONCE = 0
GENESIS_PREV_HASH = "0" * 64

EXPLORER_PORT = 8337
P2P_PORT = 9333