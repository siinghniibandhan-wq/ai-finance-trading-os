# Picomatch security patch

This vendored fork is based on upstream picomatch 4.0.7 (MIT license).
It applies the leading-quantifier ReDoS mitigation proposed in
https://github.com/micromatch/picomatch/pull/238 to repeated extglob branches.

The change literalizes repeated extglobs whose branch begins with an unanchored
bare star or question mark followed by more content. Safe anchored patterns and
bare-star branches retain their behavior. Regression tests live in
security-tests/picomatch-redos.test.cjs.

The local version 4.0.8-sb.1 identifies this project-maintained patched fork;
it is not an upstream picomatch release. Re-evaluate and remove the fork when
upstream publishes a verified patched release.
