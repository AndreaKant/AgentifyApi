const express = require('express');
const protobuf = require('protobufjs');
const app = express();

// Middleware per leggere il corpo della richiesta come testo
app.use(express.text({ type: 'text/plain' }));

app.post('/parse', (req, res) => {
    const protoContent = req.body;
    if (!protoContent) {
        return res.status(400).json({ error: 'Request body is empty' });
    }

    try {
        const { root } = protobuf.parse(protoContent, { keepCase: true });
        const functions = [];
           function findServices(namespace) {
            if (namespace instanceof protobuf.Service) {
                const serviceName = namespace.name;
                namespace.methodsArray.forEach((method) => {
                    const rpcName = method.name;
                    functions.push({
                        type: "grpc",
                        name: rpcName,
                        description: (method.comment || '').trim(),
                        metadata: {
                            name: rpcName,
                            type: "grpc",
                            service: serviceName,
                            rpc: rpcName,
                        },
                        source_contract: `rpc ${rpcName}(${method.requestType}) returns (${method.responseType}); Contratto del messaggio di richiesta (${method.requestType}): { "id": "integer" }`
                    });
                });
            }
            
            // Se il namespace ha altri sotto-namespace, esplorali
            if (namespace.nested) {
                for (const nestedName in namespace.nested) {
                    findServices(namespace.nested[nestedName]);
                }
            }
        }

        findServices(root);

        console.log(`✅ Parsed ${functions.length} gRPC functions.`);
        res.status(200).json(functions);
    } catch (error) {
        console.error('❌ Proto parsing error:', error.message);
        res.status(400).json({ error: `Parsing error: ${error.message}` });
    }
});

const PORT = 3000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 gRPC Parser is running and listening on port ${PORT}`);
});
