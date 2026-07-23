# Interview guide

## Thirty-second explanation

SeatSync is a concurrent ticket-reservation backend. A permanent Seat is
separated from ShowSeat, which stores per-show price and availability. Seat
selection is protected using an atomic conditional database update and an
expiring lock token. Payments use idempotency keys, booking status follows a
state machine, and successful confirmation writes an outbox event in the same
transaction so notifications can be retried safely.

## Questions you should be ready to answer

### Why not use an in-memory lock?
An in-memory lock only protects one process. It fails after process restart and
does not coordinate multiple API instances. The database remains the source of
truth; Redis may be added as an optimization rather than the only correctness
mechanism.

### Can payment be exactly once?
External side effects cannot generally be guaranteed exactly once. The design
uses at-least-once delivery combined with idempotency keys and idempotent state
transitions to achieve an effectively-once user outcome.

### What if payment succeeds after the lock expires?
The callback checks the booking expiry and current seat lock. It does not
confirm an expired booking. In production, the service would automatically
initiate a refund and record a reconciliation event.

### How would this scale?
- Stateless API instances behind a load balancer
- PostgreSQL primary with read replicas for catalogue reads
- Redis for cache and near-term lock metadata
- Partition show-seat data by show or date
- Kafka/RabbitMQ for outbox publication
- CDN for posters and static assets
- Rate limiting and queueing for blockbuster releases

### What would you improve next?
- Real payment gateway adapter and signed webhooks
- Refund and reconciliation workers
- Redis lock acceleration with fencing tokens
- Coupon and dynamic-pricing strategies
- Notification worker
- OpenTelemetry traces and Prometheus metrics
- Load tests against PostgreSQL using Locust or k6
