# Independent mathematical design review — cascades v0.4

Prepared 2026-10-19. This note is a design review, not a statement that a particular build has passed Stake review.

## Findings in the existing prototype

- The active bundled engine is `test-interface/engine/polska_gurom`, version `0.3.0-prototype`; the separate `polska_gurom_v0_2` model has no cascades and must remain a reference.
- Its 10,000-round diagnostic sample returned 116.6103%, so the previous 96% RTP cannot be transferred to it.
- Line awards of 0.16x and 0.25x generate final payouts off the current SDK validator's 0.1x lattice. Change the actual line paytable to multiples of 0.1x; do not round only the final book payout, because the displayed stage awards would then disagree with settlement.
- A finite population of internally valid cascade books, sampled by integer weights, is an appropriate target distribution for an RGS lookup package. Natural reel/refill probabilities are then generation inputs, not production outcome probabilities. The documentation must say this explicitly.

## A reachable maximum-win book

With the existing rotated strips, paid stops `[4, 33, 27, 21, 13]` create these rows:

```
WILD WILD WILD WILD WILD
L1   L1   L1   L1   L1
P2   P2   P2   P2   P2
```

Choose WILD for every refill. WILD is present in every refill strip, so every choice has strictly positive support. The current evaluator reaches the 5000x round cap in six evaluated cascade stages, without a bonus or the emergency cascade bound. With the unmodified prototype paytable the raw stage awards are 81.42x, then five awards of 1000x; the final credited award is capped. Revised paytable values must be evaluated again rather than retaining these amounts.

This is a valid reachable witness, even though its natural generation probability is extremely small. Assigning it a known positive lookup weight is permissible as an explicit definition of the exported distribution; it must not be described as a naturally sampled round at that frequency.

## Exact integer balancing

Let `p_i` be payout units (100 = 1x), `w_i` the nonnegative integer weights and `W = sum(w_i)`. For a cost-1x mode:

```
RTP = sum(w_i * p_i) / (100 * W)
```

Exact 96% RTP is the integer identity `sum(w_i*p_i) = 96*W`. Set `W = 10^12`; assigning 100000 mass to one maximum-win book gives exactly one maximum win per ten million paid rounds and contributes 0.0005x, or 0.05 percentage points, to RTP.

For a simple calibration preserving relative frequencies among ordinary winning books, give every ordinary winning book common weight `A`, then distribute the remaining mass over zero-payout books. If there is a valid 0.1x book, a small integer residue can be absorbed into its weight. When only 0.2x and 0.3x books are available, their payout units have gcd 10 and both can be used to resolve a multiple-of-10 residue without altering payout values. For example, represent a sufficiently large even residue using 20 units, or an odd residue (after dividing by 10) using one 30-unit award and 20-unit awards. Reserve weight/mass before solving, and assert nonnegativity, uint64 limits, exact total mass and exact RTP. Avoid putting all extra losing mass into a single book.

The exported package should report the exact hit rate, bonus/cascade rates, moments, all nonzero weights and maximum-win frequency computed from the final weights. A weight calibration changes bonus frequency if the winning and losing groups are scaled differently.

## Required interpretation of the large tests

- The 10M, 50M and 100M tests must sample the final weighted lookup distribution actually used by the local tester and exported package.
- They are not 160M fresh executions of the raw reel generator. Name this distinction in the report.
- Validate every distinct exported book against an independent line/cascade/settlement oracle before the large distribution sampling tests. This checks all reachable event sequences in the package; the large tests check their sampling frequencies and aggregate payout.
- Use independent seeds for the three sample sizes and report the actual number of draws, payout sum, hit count, maximum-win count and elapsed time. A fixed seed is a reproducibility tool, not a reason to choose favorable results.
- For a maximum-win probability 1e-7, expected cap counts are 1, 5 and 10. In 10M draws there is about a 36.8% chance of zero cap hits, so never require at least one cap in each Monte Carlo run.
- Exact weighted RTP is the mathematical result. An observed RTP plus an approximate interval is diagnostic. A simulation result above or below 96% is not itself evidence of a wrong model.
- Test autoplay separately against the running interface; drawing lookup outcomes does not prove that 100 client rounds complete or that retries are idempotent.

## Publication boundary

Local math/package validity is separate from live RGS integration and platform approval. A local virtual-balance server remains a tester until wallet authentication, resume/end-round, replay, amount scaling and required frontend review are integrated and verified.

Primary references already inspected by the project audit:

- https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py
- https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx
- https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx
