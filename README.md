# Grokking Fundamental AI Lab

## List of projects

1. Traffic Congestion Detection
2. ...

## Design Diagram
### Radio Data Collector

```mermaid
flowchart TD
    subgraph Collect
        src_1([voh-95.6])
        src_2([vov-giaothong-hcm])
        src_3([...])

        fs_1[(SeaweedFS)]

        compute_1[[M3U8 Fetcher]]
        compute_2[[FFMPEG]]

        src_1-->compute_1
        src_2-->compute_1
        src_3-->compute_1
        compute_1-->|audio file|compute_2
        compute_2-->|mono & 16khz .aac|fs_1
    end

    subgraph Compaction
    fs_2[(S3)]

    compute_3[[Tar Compressor]]
    compute_4[[Cleaner]]

    fs_1-->compute_3
    compute_3-->|Hourly block .tar.gz|fs_2
    compute_4<-.->|Remove expired files TTL|fs_1
    end

    subgraph Monitor
    alert(Telegram)
    compute_1-.->alert
    end
```

---

I do not know what I may appear to the world, but to myself I seem to have been only like a boy playing on the seashore, and diverting myself in now and then finding a smoother pebble or a prettier shell than ordinary, whilst the great ocean of truth lay all undiscovered before me.

Isaac Newton
