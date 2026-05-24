/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export → AWS Amplify can serve straight from the out/ directory.
  output: "export",
  // next/image requires the optimizer; for static export we have to disable it.
  images: { unoptimized: true },
  // Force trailing slashes so Amplify rewrites are predictable.
  trailingSlash: true,
};

export default nextConfig;
