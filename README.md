# Pitch-Range Voice-Clone Console

A listening console for the **bounded F0-budget voice-cloning task** from the ICASSP 2027
project: an utterance of source speaker A is edited towards the pitch range of target
speaker B under a hard per-frame displacement budget (`l_inf = 1.5` semitones), and the
console replays the rendered variants side by side.

Five channels per pair (all rendered by the same frozen pipeline, so the only difference
is the F0 command):

| channel | what it is |
|---|---|
| 源句子 | the untouched source utterance (speaker A) |
| 目标音域参考 | the target speaker's utterance — the pitch-range goal |
| identity | zero-edit control, re-rendered by the same chain |
| endpoint | full-budget projection (`alpha = 1`) |
| arm | the frozen selector's returned candidate |

Transport and mixing: synchronized playback of all five channels, per-channel volume,
M / S (mute / solo), a pitch-track canvas with the five F0 trajectories overlaid, and
per-clip WORLD F0 statistics (mean / P5–P95 / W1 to the target range / cap-contact
fraction).

* 20 pairs from two pools: `dev78` (ESD, 15) and `ravdess78` (RAVDESS, 5).
* Audio: 16 kHz mono PCM, rendered by the frozen P26 pass; this app only replays.
* F0 statistics were computed once on the cluster runtime (WORLD/Harvest, 10 ms frames,
  60–500 Hz) and are shipped in `data/clip_analysis.json`.
* This page supports internal listening only; it makes no listening-result claim.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Community Cloud)

1. Push this folder to a GitHub repository.
2. On <https://share.streamlit.io> → *Create app* → pick the repo, branch `main`,
   main file `app.py`.

## Provenance

Clips and statistics were produced on the project's cluster runtime from the frozen
rendering pass (`experiments/p26_listening/p26_render.py`); no selection, gate or
threshold is modified here.

## Listening safety (ear protection)

* **Master volume** slider with a hard ceiling: the top of the slider is `-1.4 dBFS`, never unity.
* **Soft limiter** on the master bus (threshold `-3 dBFS`, ratio 20) so no candidate can spike.
* **Fade in / fade out** on every play, pause and seek to remove clicks.
* LAN use: the app binds `0.0.0.0`; open `http://<mac-lan-ip>:8531` from a phone on the same Wi-Fi.
