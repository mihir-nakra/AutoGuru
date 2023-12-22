

export const init = async (useLocal) => {
    await fetch('http://127.0.0.1:5000/init', {
        'method': 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'use_local': useLocal
        })
    })
}

export const perform_inference = async (input, db_id,text_callback, source_callback) => {
    const context_response = await fetch('http://127.0.0.1:5000/get-context', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    'input_text': input,
                    'db_id': db_id
                })
            })

            const context = (await context_response.json())['context']

            for (const item of context) {
                let temp = item['metadata']['source'].split("\\")
                let pageNum = temp[temp.length - 1].split(".")[0]
                source_callback(pageNum)
            }
               
            

            const response = await fetch('http://127.0.0.1:5000/stream-inference', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({'input_text': input, 'context': context})
            })

            const reader = response.body.getReader()
            const decoder = new TextDecoder('utf-8')

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    break;
                }

                const chunk = decoder.decode(value, {stream: true})
                text_callback(chunk)
            }
}