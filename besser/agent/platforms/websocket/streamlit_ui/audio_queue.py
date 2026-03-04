import base64
import json
from typing import Any

import numpy as np
from streamlit.components.v1 import html


CONTROLLER_BOOTSTRAP = """
(function() {
    if (window.__bafAudioInit) { return; }
    window.__bafAudioInit = true;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) {
        console.warn('AudioContext not supported in this browser.');
        return;
    }
    const state = {
        queue: [],
        ctx: new AudioCtx(),
        playing: false,
        forceStop: false,
        currentSource: null,
    };

    function decodePayload(item) {
        const binary = (window.atob || atob)(item.audioBase64);
        const len = binary.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binary.charCodeAt(i);
        }
        return new Float32Array(bytes.buffer);
    }

    function playNext() {
        if (state.forceStop) {
            state.forceStop = false;
            state.playing = false;
            return;
        }

        if (!state.queue.length) {
            state.playing = false;
            return;
        }

        state.playing = true;
        const next = state.queue.shift();
        const floatArray = decodePayload(next);
        const frameCount = Math.min(next.frameCount || floatArray.length, floatArray.length);
        const buffer = state.ctx.createBuffer(1, frameCount, next.sampleRate);
        const segment = floatArray.subarray(0, frameCount);
        if (buffer.copyToChannel) {
            buffer.copyToChannel(segment, 0);
        } else {
            buffer.getChannelData(0).set(segment);
        }

        const source = state.ctx.createBufferSource();
        source.buffer = buffer;
        source.connect(state.ctx.destination);
        source.addEventListener('ended', function () {
            if (state.currentSource === source) {
                state.currentSource = null;
            }
            playNext();
        });
        source.addEventListener('error', playNext);
        state.currentSource = source;

        if (state.ctx.state === 'suspended') {
            state.ctx.resume();
        }
        source.start(0);
    }

    window.__bafAudioController = {
        enqueue(serializedItem) {
            try {
                const item = JSON.parse(serializedItem);
                state.queue.push(item);
                if (!state.playing) {
                    playNext();
                }
            } catch (err) {
                console.error('Invalid audio payload received:', err);
            }
        },
        stop() {
            state.queue.length = 0;
            state.forceStop = true;
            if (state.currentSource) {
                try { state.currentSource.stop(); } catch (e) {}
                state.currentSource.disconnect();
                state.currentSource = null;
            }
        },
    };

    window.__bafStopAudioPlayback = function () {
        if (window.__bafAudioController) {
            window.__bafAudioController.stop();
        }
    };
})();
"""


def _encode_audio_payload(audio_array: Any, sample_rate: int | float | None) -> dict[str, Any] | None:
    if audio_array is None or sample_rate is None:
        return None

    np_audio = np.asarray(audio_array)
    if np_audio.size == 0:
        return None

    float_audio = np_audio.astype(np.float32, copy=False)
    max_abs = np.max(np.abs(float_audio))
    if max_abs > 0:
        float_audio = float_audio / max_abs

    flat_audio = np.ascontiguousarray(float_audio.reshape(-1))
    audio_b64 = base64.b64encode(flat_audio.tobytes()).decode('ascii')
    return {
        "audioBase64": audio_b64,
        "sampleRate": int(sample_rate),
        "frameCount": int(flat_audio.shape[0]),
    }


def enqueue_audio_playback(audio_array: Any, sample_rate: int | float | None) -> None:
    """Queue audio data for sequential playback in the browser."""
    payload = _encode_audio_payload(audio_array, sample_rate)
    if payload is None:
        return

    payload_json = json.dumps(payload)

    controller_bootstrap_json = json.dumps(CONTROLLER_BOOTSTRAP)

    html(
        f"""
        <script>
        (function() {{
            const payload = {payload_json};
            const root = window.parent || window;

            if (!root.__bafAudioInit) {{
                try {{
                    const controllerSource = {controller_bootstrap_json};
                    const scriptEl = root.document.createElement('script');
                    scriptEl.type = 'text/javascript';
                    scriptEl.textContent = controllerSource;
                    root.document.head.appendChild(scriptEl);
                }} catch (err) {{
                    console.error('Unable to bootstrap audio controller', err);
                }}
            }}

            if (root.__bafAudioController) {{
                try {{
                    const serializedPayload = JSON.stringify(payload);
                    root.__bafAudioController.enqueue(serializedPayload);
                }} catch (err) {{
                    console.error('Unable to enqueue audio payload', err);
                }}
            }}
        }})();
        </script>
        """,
        height=0,
    )


def stop_audio_playback() -> None:
    """Stop the currently playing audio and clear the queue."""
    html(
        """
        <script>
        const root = window.parent || window;
        if (root.__bafStopAudioPlayback) {
            root.__bafStopAudioPlayback();
        }
        </script>
        """,
        height=0,
    )
