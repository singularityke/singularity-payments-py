
# Singularity Payments

A modern, type-safe TypeScript SDK for integrating M-Pesa payments into your applications. Built with developer experience in mind, featuring automatic retries, rate limiting, and comprehensive error handling.


[![License](https://img.shields.io/npm/l/@singularity-payments/core.svg)](https://github.com/yourusername/singularity-payments/blob/main/LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

## Features

-  **Easy to Use** - Simple, intuitive API that gets you up and running in minutes
-  **Type Safe** - Full TypeScript support with comprehensive type definitions
-  **Auto Retry** - Built-in retry logic with exponential backoff for failed requests
-  **Rate Limiting** - Protect your application with configurable rate limits
-  **Multiple Frameworks** - Support for Next.js, Sveltekit, Nuxt, Express, Elysia, Hono, Fastify
-  **Secure** - IP validation, duplicate prevention, and secure credential handling
-  **Lightweight** - Minimal dependencies, optimized bundle size
-  **Great Documentation** - Detailed docs with real-world examples

## Supported M-Pesa APIs

-  STK Push (Lipa Na M-Pesa Online)
- STK Query ( STK Transaction Status)
-  C2B (Customer to Business)
-  B2C (Business to Customer)
- B2B (Business to Business)
-  Account Balance
-  Transaction Status
-  Reversal
-  Dynamic QR Code Generation

## Installation


## Quick Start

### 1. Get M-Pesa Credentials

Sign up at [Safaricom Daraja Portal](https://developer.safaricom.co.ke/) and get the Sandbox:
- Consumer Key
- Consumer Secret


### 2. Set Up Environment Variables

```bash
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_ENVIRONMENT=sandbox
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback
```

### 3. Initialize Client


## Documentation

Full documentation is available at [this link](https://payments-js.singularity.co.ke)

- [Getting Started](https://docs.singularity-payments.com/getting-started)
- [STK Push Guide](https://docs.singularity-payments.com/stk-push)
- [Rate Limiting](https://docs.singularity-payments.com/rate-limiting)
- [Error Handling](https://docs.singularity-payments.com/error-handling)
- [API Reference](https://docs.singularity-payments.com/api-reference)

## Contributing


1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

-  Email:  wambua_kelvin@outlook.com
-  Issues: [GitHub Issues](https://github.com/singularity.co.ke/singularity-payments-js/issues)
-  Docs: [Documentation](https://payments-js.singularity.co.ke)

## License

Apache 2.0 © [Singularity Payments](LICENSE)

## Acknowledgments

- Built on Top of [Safaricom M-Pesa](https://developer.safaricom.co.ke/)
- Inspired by the need for better payment integrations in Africa.

## Roadmap
- [x] Comprehensive Testing for all packages(currently working on tests)
- [ ]  Demo Example
- [ ] Support for more payment providers (Airtel Money, Card Payments.)
- [ ] React Native SDK
- [ ] Prebuilt Checkout Components
- [ ] Additional Frameworks( Remix, Astro, Solid, Qwik, Angular)


