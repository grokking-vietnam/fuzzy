# Fetch HLS Stream

## Install

```bash
bash install.sh
```

## Fetching

```bash
python -m fetch_hls_stream --url M3U8_URL --output . --freq 10
```

In the case of VOH 95.6MHz, the M3U8_URL is `https://strm.voh.com.vn/radio/channel1/playlist.m3u8`

## Joining

```bash
python join_auto_files.py
```

## For Docker

```bash
bash docker_run.sh
```

## For Telegram bot

In the Telegram app, search "UtrafficBot".

## Test

```bash
pytest
```
