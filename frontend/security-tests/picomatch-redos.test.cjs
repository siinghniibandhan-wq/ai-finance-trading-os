const assert = require('node:assert/strict');
const test = require('node:test');
const picomatch = require('../vendor/picomatch');

test('literalizes single-branch repeated extglobs with unsafe leading quantifiers', () => {
  for (const pattern of ['+(*a)', '*(*a)', '+(a|*a)', '+(?[ab])']) {
    const source = picomatch.makeRe(pattern).source;
    assert.match(source, /\\\\[+*?]/, pattern + ' must be literalized');
  }
});

test('keeps safe anchored and bare-star extglobs working', () => {
  assert.equal(picomatch.isMatch('abc', '+(*)'), true);
  assert.equal(picomatch.isMatch('abc', '+(a*)'), true);
  assert.equal(picomatch.isMatch('aaa', '+(a*)'), true);
});

test('crafted non-matching strings do not trigger repeated-extglob backtracking', () => {
  const input = 'a'.repeat(10000) + '!';
  for (const pattern of ['+(*a)', '*(*a)', '+(a|*a)']) {
    assert.equal(picomatch.isMatch(input, pattern), false);
  }
});
