import { useState } from "react";
import { X, ChevronDown, Loader2 } from "lucide-react";
import type { Mission, MissionCreateDTO, MissionUpdateDTO } from "../types";
import { MapPicker } from "./MapPicker";
import { getFormError } from "../../../shared/utils/apiErrors";

interface MissionModalProps {
  mission?: Mission | null;
  onClose: () => void;
  onSave: (data: MissionCreateDTO | MissionUpdateDTO) => Promise<void>;
  availableCommanders: { id: number; name: string }[];
}

interface FormErrors {
  title?: string;
  location?: string;
  lat?: string;
  lng?: string;
  commander?: string;
  startedAt?: string;
  general?: string;
}

export function MissionModal({
  mission,
  onClose,
  onSave,
  availableCommanders,
}: MissionModalProps) {
  const isEdit = !!mission;
  const [form, setForm] = useState({
    title: mission?.title ?? "",
    commander_id: mission?.commanderId ?? "",
    location: mission?.location === "Unknown Location" ? "" : mission?.location ?? "",
    lat: "",
    lng: "",
    startedAt: mission?.startedAt ? mission.startedAt.replace(" ", "T") : "",
    notes: mission?.notes ?? "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [saving, setSaving] = useState(false);

  const inputClass =
    "w-full px-3 py-2.5 rounded-lg text-[13px] font-mono text-[#E6EAF0] placeholder-[#8A94A6] placeholder:text-[11px] outline-none transition-all focus:ring-1 focus:ring-[#C8A24A]/40";
  const inputStyleClass = "bg-[#1A2230] border border-white/10";
  const inputErrorStyleClass = "bg-[#1A2230] border border-red-500/50";
  const labelClass =
    "text-[10px] font-mono font-medium tracking-widest text-[#8A94A6] mb-1.5 block";
  const errorTextClass = "text-[10px] font-mono text-red-400 mt-1";

  function validate(): FormErrors {
    const errs: FormErrors = {};
    const trimmedTitle = form.title.trim();
    if (!trimmedTitle) {
      errs.title = "Mission title is required.";
    } else if (trimmedTitle.length < 3) {
      errs.title = "Title must be at least 3 characters.";
    }

    if (!form.commander_id) {
      errs.commander = "Commanding officer is required.";
    }

    const hasLocation = form.location.trim().length > 0;
    if (!hasLocation) {
      errs.location = "Location description is required.";
    }

    const hasLat = form.lat.trim().length > 0;
    const hasLng = form.lng.trim().length > 0;

    if (!hasLat || !hasLng) {
      errs.lat = "Coordinates are required.";
    } else {
      const latNum = parseFloat(form.lat);
      const lngNum = parseFloat(form.lng);
      if (isNaN(latNum) || latNum < -90 || latNum > 90) {
        errs.lat = "Latitude must be between -90 and 90.";
      }
      if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
        errs.lng = "Longitude must be between -180 and 180.";
      }
    }

    if (!form.startedAt) {
      errs.startedAt = "Mission date is required.";
    }

    return errs;
  }

  async function handleSubmit() {
    const validationErrors = validate();
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    const payload: Record<string, unknown> = {
      title: form.title.trim(),
      commander_id: form.commander_id ? Number(form.commander_id) : null,
      location_description: form.location.trim() || undefined,
      notes: form.notes.trim(),
      latitude: form.lat.trim(),
      longitude: form.lng.trim(),
    };

    if (form.startedAt) {
      payload.started_at = new Date(form.startedAt).toISOString();
    }

    setSaving(true);
    setErrors({});

    try {
      await onSave(payload);
    } catch (err) {
      const message = getFormError(
        err,
        "Failed to save mission. Please check your data and try again.",
      );
      setErrors({ general: message });
      setSaving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center animate-in fade-in duration-200 bg-black/70 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget && !saving) onClose();
      }}
    >
      <div
        className="w-full max-w-xl mx-4 rounded-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200 bg-[#0B0F14] border border-white/10 shadow-[0_24px_80px_rgba(0,0,0,0.6)]"
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08]"
        >
          <div>
            <div className="text-[10px] font-mono text-[#8A94A6] tracking-widest mb-0.5">
              {isEdit ? "EDIT MISSION" : "NEW MISSION"}
            </div>
            <div className="text-[16px] font-semibold text-[#E6EAF0]">
              {isEdit ? mission.title : "Create Mission Brief"}
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={saving}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all disabled:opacity-50"
          >
            <X size={16} />
          </button>
        </div>

        {/* Form */}
        <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-4">
          {/* General error banner */}
          {errors.general && (
            <div
              className="px-4 py-3 rounded-lg text-[12px] font-mono text-red-300"
              style={{
                background: "rgba(239,68,68,0.1)",
                border: "1px solid rgba(239,68,68,0.2)",
              }}
            >
              {errors.general}
            </div>
          )}

          {/* Title */}
          <div>
            <label className={labelClass}>MISSION TITLE</label>
            <input
              type="text"
              className={`${inputClass} ${errors.title ? inputErrorStyleClass : inputStyleClass}`}
              placeholder="e.g. OPERATION SILENT WATCH"
              value={form.title}
              onChange={(e) => {
                setForm({ ...form, title: e.target.value });
                if (errors.title) setErrors((prev) => ({ ...prev, title: undefined }));
              }}
            />
            {errors.title && <div className={errorTextClass}>{errors.title}</div>}
          </div>

          {/* Commander */}
          <div>
            <label className={labelClass}>COMMANDING OFFICER</label>
            <div className="relative">
              <select
                className={`${inputClass} appearance-none pr-10 cursor-pointer ${errors.commander ? inputErrorStyleClass : inputStyleClass}`}
                value={form.commander_id}
                onChange={(e) => {
                  setForm({ ...form, commander_id: e.target.value });
                  if (errors.commander) setErrors(prev => ({ ...prev, commander: undefined }));
                }}
              >
                <option value="">Select commander…</option>
                {availableCommanders.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <ChevronDown
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8A94A6] pointer-events-none"
                size={16}
              />
            </div>
            {errors.commander && <div className={errorTextClass}>{errors.commander}</div>}
          </div>

          {/* Location */}
          <div>
            <label className={labelClass}>LOCATION DESCRIPTION</label>
            <input
              type="text"
              className={`${inputClass} ${errors.location ? inputErrorStyleClass : inputStyleClass}`}
              placeholder="e.g. Grid 44T NV 834 621"
              value={form.location}
              onChange={(e) => {
                setForm({ ...form, location: e.target.value });
                if (errors.location) setErrors((prev) => ({ ...prev, location: undefined }));
              }}
            />
            {errors.location && <div className={errorTextClass}>{errors.location}</div>}
          </div>

          {/* Lat/Lng */}
          <div>
            <label className={labelClass}>COORDINATES</label>
            <div className="flex gap-2">
              <div className="flex-1">
                <input
                  type="text"
                  className={`${inputClass} ${errors.lat ? inputErrorStyleClass : inputStyleClass}`}
                  placeholder="Latitude"
                  value={form.lat}
                  onChange={(e) => {
                    setForm({ ...form, lat: e.target.value });
                    if (errors.lat) setErrors(prev => ({ ...prev, lat: undefined }));
                    if (errors.location) setErrors((prev) => ({ ...prev, location: undefined }));
                  }}
                />
              </div>
              <div className="flex-1">
                <input
                  type="text"
                  className={`${inputClass} ${errors.lng ? inputErrorStyleClass : inputStyleClass}`}
                  placeholder="Longitude"
                  value={form.lng}
                  onChange={(e) => {
                    setForm({ ...form, lng: e.target.value });
                    if (errors.lng) setErrors(prev => ({ ...prev, lng: undefined }));
                    if (errors.location) setErrors((prev) => ({ ...prev, location: undefined }));
                  }}
                />
              </div>
            </div>
          </div>

          {/* Map Picker */}
          <div>
            <label className={labelClass}>MAP PICKER</label>
            <MapPicker
              lat={form.lat}
              lng={form.lng}
              onChange={(lat, lng) => {
                setForm({ ...form, lat, lng });
                if (errors.location) setErrors((prev) => ({ ...prev, location: undefined }));
              }}
            />
          </div>

          {/* Started At */}
          <div>
            <label className={labelClass}>MISSION DATE</label>
            <input
              type="datetime-local"
              className={`${inputClass} ${errors.startedAt ? inputErrorStyleClass : inputStyleClass}`}
              value={form.startedAt}
              onChange={(e) => {
                setForm({ ...form, startedAt: e.target.value });
                if (errors.startedAt) setErrors(prev => ({ ...prev, startedAt: undefined }));
              }}
            />
            {errors.startedAt && <div className={errorTextClass}>{errors.startedAt}</div>}
          </div>

          {/* Notes */}
          <div>
            <label className={labelClass}>OPERATIONAL NOTES</label>
            <textarea
              rows={3}
              className={`${inputClass} ${inputStyleClass} resize-y`}
              placeholder="Mission objectives, ROE, special instructions…"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4 border-t border-white/[0.08]"
        >
          <button
            onClick={onClose}
            disabled={saving}
            className="px-5 py-2.5 rounded-lg text-[13px] font-mono text-[#8A94A6] hover:text-[#E6EAF0] hover:bg-white/5 transition-all disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-5 py-2.5 rounded-lg text-[13px] font-mono font-semibold transition-all bg-[#C8A24A] text-[#0B0F14] hover:bg-[#d4af5e] disabled:opacity-60 flex items-center gap-2"
          >
            {saving && <Loader2 size={14} className="animate-spin" />}
            {isEdit ? "Save Changes" : "Create Mission"}
          </button>
        </div>
      </div>
    </div>
  );
}
