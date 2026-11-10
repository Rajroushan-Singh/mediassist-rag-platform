export interface User {
    id: number;
    full_name: string;
    email: string;
}

export interface Conversation {
    id: number;
    title: string;
    created_at?: string;
    updated_at?: string;
}

export interface SourceReference {
    title: string;
    source: string;
    page?: number | null;
    url?: string | null;
    kind?: string;
}

export interface Message {
    id: number;
    role: "user" | "assistant";
    content: string;
    created_at?: string;
    sources?: SourceReference[];
    image_preview_url?: string;
    attachment_name?: string;
}

export interface HealthProfile {
    id: number;
    date_of_birth: string | null;
    biological_sex: string | null;
    health_notes: string | null;
    created_at: string;
    updated_at: string;
}

export interface MedicalCondition {
    id: number;
    condition_name: string;
    status: string;
    diagnosed_date: string | null;
    notes: string | null;
}

export interface Medication {
    id: number;
    medication_name: string;
    status: string;
    start_date: string | null;
    notes: string | null;
}

export interface Treatment {
    id: number;
    treatment_name: string;
    treatment_type: string | null;
    status: string;
    start_date: string | null;
    notes: string | null;
}

export interface ExtractedDocument {
    filename: string;
    content_type: string;
    extracted_text: string;
    warning: string | null;
    preview_url?: string;
    file_size_bytes?: number;
}

export type ConsentState = "checking" | "required" | "accepted" | "error";

