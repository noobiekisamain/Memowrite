// Memowrite for Visual Studio Code: run and check .mw programs.
const vscode = require('vscode');
const path = require('path');
const cp = require('child_process');

let terminal = null;
let diagnostics = null;

function memoCommand() {
  return vscode.workspace.getConfiguration('memowrite').get('command') || 'memowrite';
}

async function currentFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== 'memowrite') {
    vscode.window.showWarningMessage('Open a Memowrite (.mw) file first.');
    return null;
  }
  if (editor.document.isUntitled) {
    const saved = await editor.document.save();
    if (!saved) return null;
  } else if (editor.document.isDirty) {
    await editor.document.save();
  }
  return vscode.window.activeTextEditor.document.fileName;
}

async function run() {
  const file = await currentFile();
  if (!file) return;
  if (!terminal || terminal.exitStatus !== undefined) {
    terminal = vscode.window.createTerminal({ name: 'Memowrite', iconPath: vscode.Uri.file(path.join(__dirname, 'images', 'icon.png')) });
  }
  terminal.show(true);
  const cmd = memoCommand();
  const quoted = '"' + file + '"';
  terminal.sendText(process.platform === 'win32' ? `& ${cmd} ${quoted}` : `${cmd} ${quoted}`);
}

async function check() {
  const file = await currentFile();
  if (!file) return;
  cp.exec(`${memoCommand()} check "${file}"`, { cwd: path.dirname(file) }, (err, stdout, stderr) => {
    const text = (stdout || '') + (stderr || '');
    const uri = vscode.Uri.file(file);
    const m = /line (\d+): (.*)/.exec(text.replace(/\x1b\[[0-9;]*m/g, ''));
    if (m) {
      const line = Math.max(0, parseInt(m[1], 10) - 1);
      const d = new vscode.Diagnostic(new vscode.Range(line, 0, line, 1000), m[2], vscode.DiagnosticSeverity.Error);
      d.source = 'memowrite';
      diagnostics.set(uri, [d]);
      vscode.window.showErrorMessage('Memowrite: ' + m[2]);
    } else if (err && !text) {
      vscode.window.showErrorMessage('Could not run Memowrite. Is it installed? (' + err.message + ')');
    } else {
      diagnostics.set(uri, []);
      vscode.window.setStatusBarMessage('Memowrite: no mistakes found ✓', 4000);
    }
  });
}

async function studio() {
  const file = await currentFile();
  if (!file) return;
  cp.spawn(memoCommand(), ['studio', file], { detached: true, stdio: 'ignore', shell: process.platform === 'win32' }).unref();
}

function activate(context) {
  diagnostics = vscode.languages.createDiagnosticCollection('memowrite');
  context.subscriptions.push(
    diagnostics,
    vscode.commands.registerCommand('memowrite.run', run),
    vscode.commands.registerCommand('memowrite.check', check),
    vscode.commands.registerCommand('memowrite.studio', studio),
    vscode.workspace.onDidSaveTextDocument(doc => { if (doc.languageId === 'memowrite') check(); })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
