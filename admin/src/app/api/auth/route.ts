import { NextRequest, NextResponse } from "next/server";

const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD ?? "";

export async function POST(req: NextRequest) {
  if (!ADMIN_PASSWORD) {
    return NextResponse.json({ ok: true });
  }
  const { password } = (await req.json()) as { password?: string };
  if (password === ADMIN_PASSWORD) {
    return NextResponse.json({ ok: true, token: ADMIN_PASSWORD });
  }
  return NextResponse.json({ error: "口令错误" }, { status: 401 });
}
