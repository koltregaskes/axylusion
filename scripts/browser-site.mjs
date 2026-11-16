import {stat} from 'node:fs/promises';
import {resolve} from 'node:path';
export async function browserSite(args, source = resolve('.')) {
  if (args.length && (args.length !== 2 || args[0] !== '--site')) throw Error('Usage: launch-browser.mjs [--site DIRECTORY]');
  const root = resolve(args[1] || source);
  if (!(await stat(root).catch(() => null))?.isDirectory()) throw Error('Site directory does not exist: ' + root);
  return root;
}
