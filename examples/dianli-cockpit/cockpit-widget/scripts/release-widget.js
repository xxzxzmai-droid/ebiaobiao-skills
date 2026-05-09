const { spawnSync } = require('node:child_process');

const host = (process.env.EBIAOBIAO_HOST || '').replace(/\/$/, '');
const token = process.env.EBIAOBIAO_API_TOKEN || process.env.VIKA_API_TOKEN || '';
const confirm = process.argv.includes('--confirm');

if (!host) {
  console.error('Set EBIAOBIAO_HOST before release.');
  process.exit(2);
}

if (!token) {
  console.error('Set EBIAOBIAO_API_TOKEN before release.');
  process.exit(2);
}

const bin = process.platform === 'win32' ? 'widget-cli.cmd' : 'widget-cli';
const args = ['release', '--host', host, '--uploadHost', host, '--token', token, '--ci'];
const result = spawnSync(bin, args, {
  input: confirm ? 'Y\n' : undefined,
  stdio: confirm ? ['pipe', 'inherit', 'inherit'] : 'inherit',
});

process.exit(result.status || 0);
