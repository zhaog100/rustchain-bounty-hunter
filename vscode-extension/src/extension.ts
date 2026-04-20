import * as vscode from 'vscode';
import * as https from 'https';
import * as http from 'http';
import * as url from 'url';

let walletStatusBarItem: vscode.StatusBarItem;

export async function activate(context: vscode.ExtensionContext) {
    // Status bar item
    walletStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    walletStatusBarItem.command = 'rustchain.showWallet';
    context.subscriptions.push(walletStatusBarItem);

    // Commands
    const showWalletCmd = vscode.commands.registerCommand('rustchain.showWallet', () => {
        vscode.window.showInformationMessage('RustChain Wallet');
    });
    context.subscriptions.push(showWalletCmd);

    // Views
    const walletProvider = new WalletViewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(WalletViewProvider.viewType, walletProvider)
    );

    const minerProvider = new MinerViewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(MinerViewProvider.viewType, minerProvider)
    );

    const bountiesProvider = new BountiesViewProvider(context.extensionUri);
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(BountiesViewProvider.viewType, bountiesProvider)
    );

    // Auto refresh
    updateWalletStatus();
    setInterval(updateWalletStatus, 30000);
}

async function updateWalletStatus() {
    try {
        const config = vscode.workspace.getConfiguration('rustchain');
        const walletName = config.get<string>('walletName', '');
        const nodeUrl = config.get<string>('nodeUrl', 'https://rustchain.org');
        
        if (!walletName) {
            walletStatusBarItem.text = '$(warning) Set wallet in settings';
            walletStatusBarItem.tooltip = 'Configure your RustChain wallet name';
            walletStatusBarItem.show();
            return;
        }

        const balance = await fetchBalance(nodeUrl, walletName);
        walletStatusBarItem.text = `$(credit-card) ${balance} RTC`;
        walletStatusBarItem.tooltip = `RustChain Balance: ${balance} RTC`;
        walletStatusBarItem.show();
    } catch (error) {
        walletStatusBarItem.text = '$(error) RustChain';
        walletStatusBarItem.tooltip = error instanceof Error ? error.message : 'Unknown error';
        walletStatusBarItem.show();
    }
}

function fetchBalance(nodeUrl: string, walletName: string): Promise<number> {
    return new Promise((resolve, reject) => {
        const targetUrl = `${nodeUrl}/wallet/balance?miner_id=${encodeURIComponent(walletName)}`;
        const parsedUrl = url.parse(targetUrl);
        
        const options: any = {
            hostname: parsedUrl.hostname,
            port: parsedUrl.port,
            path: parsedUrl.path,
            method: 'GET',
            rejectUnauthorized: false // For self-signed certs
        };

        const client = parsedUrl.protocol === 'https:' ? https : http;
        const req = client.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    const json = JSON.parse(data);
                    resolve(json.amount_rtc || 0);
                } catch (e) {
                    reject(new Error('Invalid response'));
                }
            });
        });
        
        req.on('error', reject);
        req.setTimeout(10000, () => reject(new Error('Timeout')));
        req.end();
    });
}

class WalletViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'rustchain.wallet';
    private _view?: vscode.WebviewView;

    constructor(private readonly _extensionUri: vscode.Uri) {}

    public resolveWebviewView(webviewView: vscode.WebviewView) {
        this._view = webviewView;
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body>
            <h2>RustChain Wallet</h2>
            <div id="balance">Loading...</div>
            <script>
                const vscode = acquireVsCodeApi();
                // Balance updates come from extension host
            </script>
        </body>
        </html>`;
    }
}

// Similar providers for Miner and Bounties would go here...
class MinerViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'rustchain.miner';
    resolveWebviewView(webviewView: vscode.WebviewView) {
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = '<h2>Miner Status</h2><div>Not implemented yet</div>';
    }
}

class BountiesViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'rustchain.bounties';
    resolveWebviewView(webviewView: vscode.WebviewView) {
        webviewView.webview.options = { enableScripts: true };
        webviewView.webview.html = '<h2>Bounties</h2><div>Not implemented yet</div>';
    }
}
