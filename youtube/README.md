# YouTube Series Map

YouTube is the narrative layer for High Availability The Hard Way. Each video should send viewers back to a runnable lab or clearly say when a topic is conceptual or planned for a future lab.

## Launch Sequence

| Video | Working Title | Repo Target | Status |
|---|---|---|---|
| 1 | Your AI-generated App is Not production Ready | Overview of the repo, with Lab 2 and Lab 3 examples | Draft: `youtube/video-1.md` |
| 2 | I Broke an AI App With One Missing Timeout | `labs/02-timeouts` | Next |
| 3 | The Retry Storm That Took Down My App | `labs/03-retries-jitter` | Planned |

## CTA Pattern

Use a concrete lab command as the primary call to action:

```bash
cd labs/02-timeouts
make up
make smoke-test
make break
make load-test
make apply-fix
make load-test
```

Avoid making the reliability review bot or future PR reviewer the flagship in launch videos. The repo should lead as an educational lab system first; review automation can become a later product layer once the lab authority is established.
