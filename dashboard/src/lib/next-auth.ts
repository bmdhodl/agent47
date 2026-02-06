import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { compare } from "bcryptjs";
import sql from "@/lib/db";
import { rateLimit } from "@/lib/rate-limit";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const { ok } = rateLimit(`login:${credentials.email}`, 5, 900_000);
        if (!ok) return null;

        const rows = await sql`
          SELECT id, email, password_hash FROM users
          WHERE email = ${credentials.email}
        `;

        if (rows.length === 0) return null;

        const user = rows[0];
        const valid = await compare(credentials.password, user.password_hash);
        if (!valid) return null;

        return { id: user.id, email: user.email };
      },
    }),
  ],
  session: { strategy: "jwt" },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.userId = user.id;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as { id?: string }).id = token.userId as string;
      }
      return session;
    },
  },
};
