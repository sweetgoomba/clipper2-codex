"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.parseDarwinMemory = parseDarwinMemory;
exports.observeAdmissionMemory = observeAdmissionMemory;
const node_child_process_1 = require("node:child_process");
const node_os_1 = require("node:os");
const node_util_1 = require("node:util");
const exec = (0, node_util_1.promisify)(node_child_process_1.execFile);
const MiB = 1024 ** 2;
function unavailable(free) {
    return { observed_at: new Date().toISOString(), source: 'unavailable', pressure: 'unknown', free_bytes: Number.isSafeInteger(free) && free >= 0 ? free : 0, budget_bytes: 0 };
}
function parseDarwinMemory(vm, pressureValue, free, total) {
    const missing = unavailable(free);
    const pageSize = Number(vm.match(/page size of (\d+) bytes/)?.[1]);
    const pages = (name) => Number(vm.match(new RegExp('^' + name + ':\\s+(\\d+)\\.\\s*$', 'm'))?.[1]);
    const counts = [pages('Pages free'), pages('File-backed pages'), pages('Pages purgeable')];
    if (!Number.isSafeInteger(total) || total <= 0 || !Number.isSafeInteger(free) || free < 0 || free > total ||
        !Number.isSafeInteger(pageSize) || pageSize <= 0 || counts.some(n => !Number.isSafeInteger(n) || n < 0 || n > total / pageSize))
        return missing;
    const [vmFree, fileBacked, purgeable] = counts.map(n => n * pageSize);
    if (vmFree + fileBacked > total)
        return missing;
    const level = pressureValue.trim();
    const pressure = level === '1' ? 'normal' : level === '2' ? 'warning' : level === '4' ? 'critical' : null;
    if (!pressure)
        return missing;
    // XNU identifies free/file-backed/purgeable pages as reclaimable. Do not add
    // inactive, speculative (already in free), compressed or total RAM. Count at
    // most half the larger cache pool, avoiding any possible overlap, and leave
    // 512 MiB plus a pressure-dependent margin for the OS and CPU work.
    const freeBytes = Math.min(free, vmFree);
    const headroom = Math.max(0, freeBytes + Math.max(fileBacked, purgeable) * .5 - 512 * MiB);
    return { observed_at: new Date().toISOString(), source: 'darwin_vm', pressure, free_bytes: freeBytes,
        file_backed_bytes: fileBacked, purgeable_bytes: purgeable,
        budget_bytes: pressure === 'critical' ? 0 : Math.floor(headroom * (pressure === 'warning' ? .5 : .7)) };
}
async function observeAdmissionMemory() {
    if (process.platform !== 'darwin') {
        const free = (0, node_os_1.freemem)();
        return Number.isSafeInteger(free) && free >= 0
            ? { observed_at: new Date().toISOString(), source: 'os_free', pressure: 'unknown', free_bytes: free, budget_bytes: Math.floor(free * .7) } : unavailable(free);
    }
    try {
        const [vm, pressure] = await Promise.all([
            exec('/usr/bin/vm_stat', [], { timeout: 1000, maxBuffer: 32 * 1024, env: { ...process.env, LC_ALL: 'C' } }),
            exec('/usr/sbin/sysctl', ['-n', 'kern.memorystatus_vm_pressure_level'], { timeout: 1000, maxBuffer: 1024 }),
        ]);
        return parseDarwinMemory(vm.stdout, pressure.stdout, (0, node_os_1.freemem)(), (0, node_os_1.totalmem)());
    }
    catch {
        return unavailable((0, node_os_1.freemem)());
    }
}
//# sourceMappingURL=memory.js.map