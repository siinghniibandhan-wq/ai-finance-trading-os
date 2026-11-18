const assert = require('node:assert/strict');
const test = require('node:test');
const picomatch = require('../vendor/picomatch');

test('literalizes repeated extglobs containing glob stars', () => {
  const vulnerablePatterns = [
    '+(*)', '+(*a)', '+(a*)', '+(a*a)', '+(*)a',
    '*(*)', '*(*a)', '*(a*|b)', '+(a|*a)'
  ];
  for (const pattern of vulnerablePatterns) {
    const source = picomatch.makeRe(pattern).source;
    assert.ok(source.includes('\\\\+(') || source.includes('\\\\*('), pattern + ' must be literalized');
  }
});

test('literalizes repeated extglobs with repeated-branch overlap', () => {
  for (const pattern of ['+(ab|abab)', '+(abc|abcabc)']) {
    const source = picomatch.makeRe(pattern).source;
    assert.ok(source.includes('\\\\+('), pattern + ' must be literalized');
  }
});

test('preserves safe extglob behavior', () => {
  assert.equal(picomatch.isMatch('jsjsx', '+(js|jsx)'), true);
  assert.equal(picomatch.isMatch('foofoobar', '+(foo|foobar)'), true);
  assert.equal(picomatch.isMatch('fff', '*(f)'), true);
  assert.equal(picomatch.isMatch('fffooo', '*(*(f)*(o))'), true);
});

test('crafted non-matching strings do not trigger repeated-extglob backtracking', () => {
  const input = 'a'.repeat(10000) + '!';
  for (const pattern of ['+(*a)', '+(*)a', '+(a*)', '*(a*|b)']) {
    assert.equal(picomatch.isMatch(input, pattern), false);
  }
});
