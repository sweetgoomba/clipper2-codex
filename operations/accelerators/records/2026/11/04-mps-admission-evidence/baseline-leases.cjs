"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VerificationAuthorizations = exports.AcceleratorLeases = void 0;
const node_http_1 = require("node:http");
const node_crypto_1 = require("node:crypto");
const node_os_1 = require("node:os");
const node_child_process_1 = require("node:child_process");
const node_util_1 = require("node:util");
const exec = (0, node_util_1.promisify)(node_child_process_1.execFile);
class AcceleratorLeases {
    adapters;
    ancestor;
    authorizations;
    server = null;
    token = (0, node_crypto_1.randomUUID)();
    leases = new Map();
    timer = null;
    constructor(adapters, ancestor = process.pid, authorizations) {
        this.adapters = adapters;
        this.ancestor = ancestor;
        this.authorizations = authorizations;
    }
    async start() {
        this.server = (0, node_http_1.createServer)((q, s) => { void this.handle(q, s); });
        await new Promise(r => this.server.listen(0, '127.0.0.1', r));
        this.server.unref();
        this.timer = setInterval(() => this.expire(), 1000);
        this.timer.unref();
        const address = this.server.address();
        if (!address || typeof address === 'string')
            throw new Error('lease host address');
        return { CLIPPER_ACCELERATOR_HOST_URL: `http://127.0.0.1:${address.port}`, CLIPPER_ACCELERATOR_HOST_TOKEN: this.token };
    }
    async stop() { if (this.timer)
        clearInterval(this.timer); this.leases.clear(); if (this.server)
        await new Promise(r => this.server.close(() => r())); }
    expire() {
        for (const [id, lease] of this.leases) {
            for (const pid of lease.workers)
                if (!alive(pid))
                    lease.workers.delete(pid);
            lease.stale = lease.expires < Date.now();
            // Silence never proves that native calls or device allocations ended.
            if ((!alive(lease.owner) || lease.released && !lease.nativeOwner) && lease.workers.size === 0)
                this.leases.delete(id);
        }
    }
    fits(bytes, adapter) {
        if (!Number.isSafeInteger(bytes) || Number(bytes) < 0 || Number(bytes) > (0, node_os_1.freemem)() * .7)
            return false;
        if (adapter.memory_kind === 'dedicated' && (typeof adapter.free_bytes !== 'number' || Number(bytes) > adapter.free_bytes * .7))
            return false;
        return true;
    }
    async handle(req, res) {
        const send = (status, value) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(value)); };
        if (req.headers.authorization !== `Bearer ${this.token}`) {
            send(401, {});
            return;
        }
        if (req.method !== 'POST') {
            send(405, {});
            return;
        }
        try {
            let text = '';
            for await (const chunk of req) {
                text += chunk;
                if (Buffer.byteLength(text) > 4096) {
                    send(413, {});
                    return;
                }
            }
            const body = JSON.parse(text);
            this.expire();
            if (req.url === '/validate-test') {
                if (!Number.isSafeInteger(body.owner_pid) || !this.authorizations?.authorize(body.token, body.consumer, body.job_id, body.owner_pid, false) || !await descendant(body.owner_pid, this.ancestor)) {
                    send(403, { error: 'verification_not_authorized' });
                    return;
                }
                send(this.authorizations.authorize(body.token, body.consumer, body.job_id, body.owner_pid, true) ? 200 : 403, { ok: true });
                return;
            }
            if (req.url === '/acquire') {
                if (!Number.isSafeInteger(body.owner_pid) || body.owner_pid <= 0 || typeof body.adapter_id !== 'string') {
                    send(400, { error: 'unverified_adapter_or_owner' });
                    return;
                }
                const adapter = (await this.adapters()).find(a => a.id === body.adapter_id);
                if (!adapter) {
                    send(400, { error: 'unverified_adapter' });
                    return;
                }
                if (!this.fits(body.estimated_bytes, adapter)) {
                    send(409, { error: 'memory_admission_deferred' });
                    return;
                }
                if (!await descendant(body.owner_pid, this.ancestor)) {
                    send(403, { error: 'owner_not_app_child' });
                    return;
                }
                if ([...this.leases.values()].some(v => v.adapter === body.adapter_id)) {
                    send(409, { error: 'adapter_busy' });
                    return;
                }
                const lease = { id: (0, node_crypto_1.randomUUID)(), adapter: body.adapter_id, owner: body.owner_pid, expires: Date.now() + 15_000, bytes: body.estimated_bytes, workers: new Set() };
                this.leases.set(lease.id, lease);
                send(200, { lease_id: lease.id });
                return;
            }
            const lease = this.leases.get(body.lease_id);
            if (!lease || lease.owner !== body.owner_pid) {
                send(410, { error: 'lease_expired' });
                return;
            }
            if (req.url === '/register-native') {
                lease.nativeOwner = true;
            }
            else if (req.url === '/register-worker') {
                if (!Number.isSafeInteger(body.worker_pid) || body.worker_pid === lease.owner || !await descendant(body.worker_pid, lease.owner)) {
                    send(403, { error: 'worker_not_owned' });
                    return;
                }
                lease.workers.add(body.worker_pid);
            }
            else if (req.url === '/reserve') {
                const adapter = (await this.adapters()).find(a => a.id === lease.adapter);
                if (!adapter || !Number.isSafeInteger(body.estimated_bytes) || Number(body.estimated_bytes) < 0 || !this.fits(lease.bytes + body.estimated_bytes, adapter)) {
                    send(409, { error: 'memory_admission_deferred' });
                    return;
                }
                lease.bytes += body.estimated_bytes;
            }
            else if (req.url === '/heartbeat')
                lease.expires = Date.now() + 15_000;
            else if (req.url === '/validate') { /* read-only lease validation */ }
            else if (req.url === '/release') {
                lease.released = true;
                this.expire();
            }
            else {
                send(404, {});
                return;
            }
            send(200, { ok: true });
        }
        catch {
            send(400, { error: 'invalid_request' });
        }
    }
}
exports.AcceleratorLeases = AcceleratorLeases;
function alive(pid) { try {
    process.kill(pid, 0);
    return true;
}
catch (error) {
    return error.code !== 'ESRCH';
} }
async function descendant(pid, ancestor) {
    for (let i = 0; i < 12 && pid > 1; i++) {
        if (pid === ancestor)
            return true;
        try {
            const value = process.platform === 'win32'
                ? await exec('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', `(Get-CimInstance Win32_Process -Filter 'ProcessId=${pid}').ParentProcessId`], { timeout: 2000, windowsHide: true })
                : await exec('/bin/ps', ['-o', 'ppid=', '-p', String(pid)], { timeout: 2000 });
            pid = Number(value.stdout.trim());
            if (!Number.isSafeInteger(pid))
                return false;
        }
        catch {
            return false;
        }
    }
    return false;
}
class VerificationAuthorizations {
    grants = new Map();
    issue(plugin, job) {
        if (!['dance_highlight', 'person_highlight', 'dialog_highlight'].includes(plugin) || !job || job.length > 200)
            throw new Error('invalid verification scope');
        for (const [key, value] of this.grants)
            if (value.expires < Date.now())
                this.grants.delete(key);
        const token = (0, node_crypto_1.randomBytes)(32).toString('hex');
        this.grants.set(token, { consumer: plugin.replace(/_highlight$/, ''), job, expires: Date.now() + 21_600_000 });
        return token;
    }
    authorize(token, consumer, job, owner, claim) {
        if (typeof token !== 'string')
            return false;
        const grant = this.grants.get(token);
        if (!grant || grant.expires < Date.now() || grant.consumer !== consumer || grant.job !== job || (grant.owner !== undefined && grant.owner !== owner))
            return false;
        if (claim)
            grant.owner = owner;
        return true;
    }
}
exports.VerificationAuthorizations = VerificationAuthorizations;
//# sourceMappingURL=leases.js.map