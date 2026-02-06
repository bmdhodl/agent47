export { default } from "next-auth/middleware";

export const config = {
  matcher: [
    "/traces/:path*",
    "/alerts/:path*",
    "/usage/:path*",
    "/settings/:path*",
  ],
};
