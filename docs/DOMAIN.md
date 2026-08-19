# Domain setup

The repository deploys the public site through GitHub Pages with `sovrune.com` as its custom domain.

Configure the apex domain with GitHub Pages' current apex records and configure `www` as a CNAME to `sovrune.github.io`. DNS records can change; verify the values in GitHub's official Pages documentation before applying them. After DNS resolves, enable **Enforce HTTPS** in repository Pages settings.

Email is separate from website hosting. Configure `hello@sovrune.com`, `security@sovrune.com`, and `conduct@sovrune.com` with the chosen mail provider before publishing those addresses broadly.
