# Core Web Vitals

| Field metric | Good | Needs improvement | Poor |
|---|---:|---:|---:|
| Largest Contentful Paint (LCP) | ≤2.5 s | >2.5 s and ≤4.0 s | >4.0 s |
| Interaction to Next Paint (INP) | ≤200 ms | >200 ms and ≤500 ms | >500 ms |
| Cumulative Layout Shift (CLS) | ≤0.1 | >0.1 and ≤0.25 | >0.25 |

Assess field data at the 75th percentile. For CrUX, record the URL or origin scope, device, and reporting window. Lack of samples or an origin fallback limits URL-level conclusions. Keep comparable test conditions when comparing lab runs. Total Blocking Time diagnoses lab main-thread work and cannot stand in for field INP. Raw HTML can suggest improvements such as early hero discovery, dimensions for late-loading content and deferring noncritical work. It cannot establish timings or layout shifts.

Confirm with current [Web Vitals guidance](https://web.dev/articles/vitals) and [CrUX documentation](https://developer.chrome.com/docs/crux).
