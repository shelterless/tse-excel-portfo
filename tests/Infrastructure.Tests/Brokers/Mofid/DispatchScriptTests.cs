using System.Diagnostics;
using System.Text.Json;
using TseExcel.Infrastructure.Brokers.Mofid;
using Xunit;

namespace TseExcel.Infrastructure.Tests.Brokers.Mofid;

public class DispatchScriptTests
{
    [Fact]
    public async Task BrowserScripts_StopFutureInitiationsWithoutAbortingPendingRequestsOrReplaying()
    {
        // Execute the actual bridge scripts with the already bundled Playwright Node runtime.
        // All browser globals, time and fetch are deterministic fakes; no network is available to this fixture.
        string script = "const prepare = " + ChromeMofidBrowser.PrepareDispatchScript + ";\n" +
            "const initiate = " + ChromeOrderDispatch.InitiateScript + ";\n" +
            "const stop = " + ChromeOrderDispatch.StopScript + ";\n" + "const payload = " +
            JsonSerializer.Serialize("{\"order\":{\"createDateTime\":\"__TSE_LOCAL_TIMESTAMP__\"}}") + ";\n" + """
            const assert = require('node:assert/strict');
            global.window = {};
            let now = 1000, timer, calls = 0, pending = 0;
            Date.now = () => now;
            global.performance = {timeOrigin:1000, now:() => now - 1000};
            global.setTimeout = callback => { timer = callback; return 1; };
            global.clearTimeout = () => {};
            global.fetch = (url, options) => {
              calls++; pending++;
              assert.equal(url, 'https://fixture.invalid/order');
              assert.equal(options.method, 'POST');
              assert.equal(options.signal, undefined);
              return new Promise(() => {});
            };
            const args = {payload, headers:{}, url:'https://fixture.invalid/order', cutoff:2000};
            for (const mode of ['cancel', 'cutoff', 'dispose']) {
              now = 1000; prepare(args);
              const before = calls;
              assert.equal(initiate().initiated, true);
              assert.equal(initiate().initiated, true);
              assert.equal(calls, before + 2); // Unresolved responses never serialize initiations.
              const inFlight = pending;
              if (mode === 'cancel') window.__tseOpening.stop();
              if (mode === 'cutoff') { now = 2000; timer(); }
              if (mode === 'dispose') stop();
              assert.equal(initiate().initiated, false);
              assert.equal(pending, inFlight);
              assert.equal(calls, before + 2);
              stop();
            }
            now = 1000; prepare(args);
            global.fetch = () => { calls++; throw new Error('sanitized fixture'); };
            const before = calls;
            assert.equal(initiate().failed, true);
            assert.equal(calls, before + 1); // A synchronous initiation failure is never retried.
            stop();
            assert.equal(initiate().initiated, false);
            assert.equal(calls, before + 1);
            console.log('Dispatch script assertions passed.');
            """;
        await RunNodeAsync(script, "Dispatch script assertions passed.");
    }

    [Fact]
    public async Task ReadScript_ClassifiesAuthenticationTransportAndMalformedDataWithoutReturningPrivateBodies()
    {
        string script = "const read = " + ChromeMofidBrowser.ReadScript + ";\n" + """
            const assert = require('node:assert/strict');
            let response;
            global.setTimeout = () => 1;
            global.clearTimeout = () => {};
            global.fetch = async () => response;
            const args = {url:'https://fixture.invalid/read', headers:{}, method:'GET', maximumBytes:10};
            function fixture(status = 200, contentType = 'application/json', bytes = new TextEncoder().encode('{}')) {
              let done = false;
              return {status, ok: status >= 200 && status < 300, headers: {get: () => contentType},
                body:{getReader:() => ({read:async () => done ? {done:true} : (done = true, {done:false, value:bytes}), cancel:async () => {}})}};
            }
            (async () => {
              for (const status of [401, 403]) {
                response = fixture(status);
                assert.deepEqual(await read(args), {ok:false, authentication:true});
              }
              response = fixture(500);
              assert.deepEqual(await read(args), {ok:false});
              for (const contentType of ['text/html', 'application/json-unverified']) {
                response = fixture(200, contentType);
                assert.deepEqual(await read(args), {ok:false, malformed:true});
              }
              response = fixture(200, 'application/json', new Uint8Array(11));
              assert.deepEqual(await read(args), {ok:false, malformed:true});
              response = fixture(200, 'application/json', new Uint8Array([255]));
              assert.deepEqual(await read(args), {ok:false, malformed:true});
              response = fixture(); response.body = null;
              assert.deepEqual(await read(args), {ok:false, malformed:true});
              response = fixture(200, 'application/json; charset=utf-8');
              assert.deepEqual(await read(args), {ok:true, body:'{}'});
              global.fetch = async () => { throw new Error('private fixture data'); };
              assert.deepEqual(await read(args), {ok:false});
              console.log('Read script assertions passed.');
            })().catch(error => { console.error(error); process.exitCode = 1; });
            """;
        await RunNodeAsync(script, "Read script assertions passed.");
    }

    private static async Task RunNodeAsync(string script, string expected)
    {
        string node = Path.Combine(AppContext.BaseDirectory, ".playwright", "node", "win32_x64", "node.exe");
        Assert.True(File.Exists(node));
        using var process = new Process { StartInfo = new ProcessStartInfo(node)
            { RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false, CreateNoWindow = true } };
        process.Start();
        await process.StandardInput.WriteAsync(script);
        process.StandardInput.Close();
        Task<string> output = process.StandardOutput.ReadToEndAsync(), error = process.StandardError.ReadToEndAsync();
        try { await process.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(15)); }
        finally { if (!process.HasExited) process.Kill(entireProcessTree: true); }
        Assert.True(process.ExitCode == 0, await error);
        Assert.Contains(expected, await output);
    }
}
