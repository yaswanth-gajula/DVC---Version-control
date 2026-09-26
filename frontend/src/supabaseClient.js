import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

// This client is used ONLY for Supabase Auth (sign up, sign in, sign out,
// session management). The frontend never queries Supabase tables or
// storage directly -- all project/version data goes through the FastAPI
// backend, which uses the service_role key. The anon key here can only
// ever do what Supabase Auth itself permits.
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);