# MQTT with Mutual TLS (mTLS) Authentication

This project demonstrates a secure MQTT setup using mutual TLS (mTLS) authentication between an MQTT broker (Mosquitto) and clients. The implementation uses Docker for containerization and includes both the broker and a Python client.

## Project Structure

```
.
├── docker-compose.yml          # Docker composition file
├── generate-certs.sh          # Script to generate TLS certificates
├── client/                    # MQTT client implementation
│   ├── client.py             # Python MQTT client with mTLS support
│   └── Dockerfile            # Client container configuration
└── mosquitto/                # MQTT broker configuration
    ├── certs/                # TLS certificates directory
    ├── config/               # Broker configuration
    │   └── mosquitto.conf    # Mosquitto configuration file
    ├── data/                 # Persistent data storage
    └── log/                  # Broker logs
```

## Security Features

- Mutual TLS (mTLS) authentication
- Client certificate verification
- No anonymous connections allowed
- Client identity verification using certificates
- Secure communication over port 8883 (MQTT over TLS)

## Certificate Generation

The project includes a `generate-certs.sh` script that creates all necessary certificates for the mTLS setup. Here's what it does:

1. **Certificate Authority (CA)**
   - Generates a CA private key (`ca.key`)
   - Creates a self-signed CA certificate (`ca.crt`)
   - Valid for 10 years (3650 days)

2. **Broker Certificate**
   - Generates server private key (`server.key`)
   - Creates Certificate Signing Request (CSR) for the broker
   - Signs the CSR with the CA to create the server certificate (`server.crt`)
   - Valid for 1 year (365 days)

3. **Client Certificate**
   - Generates client private key (`client.key`)
   - Creates Certificate Signing Request (CSR) for the client
   - Signs the CSR with the CA to create the client certificate (`client.crt`)
   - Valid for 1 year (365 days)

## Broker Configuration (Mosquitto)

The Mosquitto broker is configured with strict security settings:

```properties
listener 8883                    # MQTT over TLS port
cafile /mosquitto/certs/ca.crt  # CA certificate for client verification
certfile /mosquitto/certs/server.crt  # Server certificate
keyfile /mosquitto/certs/server.key   # Server private key
require_certificate true         # Require client certificates
use_identity_as_username true   # Use certificate CN as username
allow_anonymous false           # No anonymous connections
```

## Client Implementation

The Python client (`client.py`) implements a robust MQTT client with the following features:

- TLS 1.2 with certificate verification
- Automatic reconnection with exponential backoff
- Health check publishing
- Last Will and Testament (LWT) for connection status
- Structured logging
- Clean shutdown handling

### Client Features:
- Automatic reconnection with configurable retry attempts
- Exponential backoff for connection retries
- Health status monitoring via `$SYS/health` topic
- Message publishing with QoS control
- Detailed logging of all operations
- Graceful shutdown handling

## Setting Up Multiple Clients

To set up multiple clients with their own certificates:

1. **Generate Additional Client Certificates**
   ```bash
   # Generate new client key
   openssl genrsa -out mosquitto/certs/client2.key 2048
   
   # Create CSR with unique client name
   openssl req -new -key mosquitto/certs/client2.key -out mosquitto/certs/client2.csr -subj "/CN=client2"
   
   # Sign certificate with CA
   openssl x509 -req -in mosquitto/certs/client2.csr -CA mosquitto/certs/ca.crt -CAkey mosquitto/certs/ca.key -CAcreateserial -out mosquitto/certs/client2.crt -days 365 -sha256
   ```

2. **Create New Client Container**
   - Copy the client directory for each new client
   - Update the certificate paths in the client configuration
   - Add the new service to `docker-compose.yml`

Example docker-compose addition for a new client:
```yaml
  mqtt-client2:
    build:
      context: ./client
      dockerfile: Dockerfile
    volumes:
      - ./mosquitto/certs/ca.crt:/certs/ca.crt
      - ./mosquitto/certs/client2.crt:/certs/client.crt
      - ./mosquitto/certs/client2.key:/certs/client.key
    depends_on:
      - mosquitto
```

## Running the Project

1. Generate certificates:
   ```bash
   ./generate-certs.sh
   ```

2. Start the services:
   ```bash
   docker-compose up -d
   ```

3. Monitor logs:
   ```bash
   docker-compose logs -f
   ```

## Security Considerations

- Keep private keys secure and never commit them to version control
- Regularly rotate certificates (they are set to expire after 1 year)
- Monitor broker logs for unauthorized access attempts
- Use strong passwords for private keys in production
- Consider implementing certificate revocation lists (CRL) for production use
- Back up the CA private key securely

## Development and Testing

For development and testing purposes:
1. All certificates are stored in the `mosquitto/certs` directory
2. The broker and client containers share certificate volumes
3. Logs are accessible in the `mosquitto/log` directory
4. Client messages and connection status can be monitored via the broker logs

## License

CC BY
