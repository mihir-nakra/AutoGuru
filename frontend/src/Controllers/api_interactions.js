const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const perform_inference = async (input, db_id, text_callback, source_callback) => {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ input_text: input, db_id: db_id }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        let currentEvent = null;
        for (const line of lines) {
            if (line.startsWith('event:')) {
                currentEvent = line.slice(6).trim();
            } else if (line.startsWith('data:') && currentEvent) {
                const jsonStr = line.slice(5).trim();
                try {
                    const data = JSON.parse(jsonStr);
                    if (currentEvent === 'token' && data.token) {
                        text_callback(data.token);
                    } else if (currentEvent === 'sources' && data.pages) {
                        for (const page of data.pages) {
                            source_callback(page);
                        }
                    }
                } catch (e) {
                    // ignore malformed JSON
                }
                currentEvent = null;
            }
        }
    }
};

export const init = async () => {
    // No-op: Bedrock LLM doesn't need initialization
};

export const fetchVehicles = async () => {
    const response = await fetch(`${API_BASE}/vehicles`);
    if (!response.ok) throw new Error('Failed to fetch vehicles');
    return response.json();
};

export const addManual = async (link, make, model, year) => {
    const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ link, make, model, year }),
    });

    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Upload failed');
    }
    return response.json();
};
