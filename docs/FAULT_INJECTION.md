# Fault Injection and Stress Campaigns

`synapdrive_ai.stress` contains deterministic signal fault injection for verification. It is designed to test whether defined bad-input conditions trigger the expected fail-closed behavior.

Implemented injectors include:

* Gaussian noise;
* contiguous dropout;
* amplitude clipping;
* line-frequency contamination;
* channel swaps.

Run the built-in campaign:

```text
synapdrive-stress --runs 100 --seed 7
```

A campaign reports every trial, its measured signal-quality score/state, whether policy expected it to block, whether the callback actually blocked, and whether the invariant passed.

The stress harness is not a proof of safety against every possible sensor or software failure. It is an extensible negative-control surface.
