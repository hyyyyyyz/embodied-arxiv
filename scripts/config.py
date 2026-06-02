"""Constants shared by the daily fetch + build scripts.

Edit DIRECTIONS to refine coverage; everything else (arxiv query, scoring
defaults) reads from here so the /research-assistant skill stays declarative.
"""

from __future__ import annotations

# Arxiv categories we sweep each day. Order doesn't matter; arxiv ORs them.
# - cs.RO: Robotics (VLA, embodied policies)
# - cs.CV: Computer Vision (VGGT, 3D reconstruction, foundation models)
# - cs.LG: Machine Learning (world models, latent dynamics)
# - cs.AI: AI generic (multi-agent, planning, foundation models for embodied)
# - cs.CL: Computation & Language (VLM backbones used by VLA)
# - cs.MM: Multimedia (multimodal benchmarks)
ARXIV_CATEGORIES: list[str] = ["cs.RO", "cs.CV", "cs.LG", "cs.AI", "cs.CL", "cs.MM"]

# Each direction is matched by a set of lowercase substring keywords. A paper
# is kept if ANY keyword for a direction appears in title OR abstract; the
# direction that matched (with the most distinct hits) becomes matched_domain.
#
# Tweak these lists when a recurring noisy paper sneaks in or when a niche
# subtopic needs coverage. Order = display preference on ties.
DIRECTIONS: dict[str, list[str]] = {
    "VLA": [
        "vision-language-action",
        "vision language action",
        "vla model",
        "vla policy",
        "robot policy",
        "embodied policy",
        "manipulation policy",
        "robotic manipulation",
        "openvla",
        "rt-2",
        "rt2",
        "pi-0",
        "pi0",
        "language-conditioned policy",
        "instruction-following manipulation",
    ],
    "World Model": [
        "world model",
        "world models",
        "neural simulator",
        "latent dynamics",
        "dynamics model",
        "video prediction",
        "video generation for robotics",
        "video world model",
        "genie",
        "navworld",
        "dreamerv3",
        "policy world model",
    ],
    "WAM": [
        "world action model",
        "wam ",
        "action world model",
        "joint action prediction",
        "unified action model",
    ],
    "VGGT": [
        "vggt",
        "vggsfm",
        "dust3r",
        "mast3r",
        "feed-forward 3d",
        "feedforward 3d",
        "3d foundation model",
        "monocular 3d reconstruction",
        "novel view synthesis",
        "neural radiance",
        "gaussian splatting",
        "3d scene reconstruction",
        "geometry grounded",
        "visual geometry",
    ],
    "Agent": [
        "llm agent",
        "llm-based agent",
        "llm-powered agent",
        "embodied agent",
        "multi-agent",
        "multi agent",
        "agentic",
        "agent framework",
        "react agent",
        "reasoning and acting",
        "tool-use agent",
        "tool use agent",
        "gui agent",
        "web agent",
        "planning agent",
        "language agent",
        "foundation model agent",
        "agentic workflow",
        "autonomous agent",
        "agent benchmark",
    ],
    "Diffusion": [
        "diffusion policy",
        "diffusion model",
        "diffusion transformer",
        " dit ",
        "denoising diffusion",
        "flow matching",
        "latent diffusion",
        "consistency model",
        "score-based",
        "score based generative",
        "rectified flow",
        "video diffusion",
        "stable diffusion",
        "diffusion-based",
        "diffusion based policy",
        "image diffusion",
        "guided diffusion",
        "classifier-free guidance",
    ],
    "Multi-modal": [
        "multimodal large language model",
        "multi-modal large language model",
        "mllm",
        "vision-language model",
        "vision language model",
        "vlm",
        "video-llm",
        "video llm",
        "audio-visual",
        "embodied chain-of-thought",
        "spatial reasoning",
        "embodied reasoning",
        "long-horizon planning",
    ],
}

# Default daily cap. If arxiv returns more matching papers than this, we keep
# the highest-recency cluster — the skill prompt can override via --max.
MAX_PAPERS_PER_DAY: int = 60

# UA string for HTTP requests. arxiv rate-limits aggressively without one.
USER_AGENT: str = "embodied-arxiv/0.1 (Claude Code skill; +https://hyyyyyyz.github.io/embodied-arxiv)"

# How to interpret a "day" — arxiv ships UTC, we live in HKT (UTC+8). The
# announcement at 00:00 UTC = 08:00 HKT, so a calendar date in HKT typically
# corresponds to the previous UTC date's announcement window.
ARXIV_TIMEZONE_OFFSET_HOURS: int = 8  # HKT/CST

# Sentinel files
SEEN_DB: str = "data/seen.json"
RAW_DIR: str = "data/raw"
CARDS_DIR: str = "data/cards"
WEB_DATA_DIR: str = "web/public/data"
WEB_PAPERS_DIR: str = "web/public/data/papers"

# Obsidian vault
OBSIDIAN_ROOT: str = "/Users/jacksonhuang/ObsidianVault-arxiv/embodied-arxiv"
OBSIDIAN_DAILY: str = "DailyPapers"
OBSIDIAN_PAPERS: str = "Papers"
