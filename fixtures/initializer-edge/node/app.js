// This module's OWN top level performs no effect. It requires a dependency whose top level reads env.
const dep = require('effectful-dep');
module.exports = { n: 1 };
