# Picomatch security patch

This vendored fork is based on upstream picomatch 4.0.7 (MIT license).
It applies the comprehensive repeated-extglob ReDoS mitigation proposed in
https://github.com/micromatch/picomatch/pull/235. The patch detects glob stars
inside repeated extglob branches and repeated-branch overlap that can create
catastrophic regular-expression backtracking.

Regression tests cover the reported vulnerable patterns and preserve safe
extglob cases in security-tests/picomatch-redos.test.cjs.

The local version 4.0.8-sb.1 identifies this project-maintained patched fork;
it is not an upstream picomatch release. Re-evaluate and remove the fork when
upstream publishes a verified patched release.
