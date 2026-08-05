import { useState } from "react";
import type { FormEvent } from "react";
import { Plus } from "lucide-react";

import { Button } from "../../../admin/components/Button";
import { Modal } from "../../../admin/components/Modal";
import { ModalActions } from "../../../admin/components/ModalActions";
import {
  SelectField,
  TextAreaField,
  TextField,
} from "../../../admin/components/FormFields";
import { createDefect } from "../../api/repairsApi";
import {
  DEFECT_TYPE_OPTIONS,
  SEVERITY_OPTIONS,
} from "../../constants/repairsCatalog";
import {
  localDatetimeToIso,
  toLocalDatetimeInput,
} from "../../utils/repairsFormat";
import { isAbortError } from "../../../../shared/api/apiClient";
import {
  getApiFieldError,
  getFormError,
} from "../../../../shared/utils/apiErrors";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";

import type { DefectSeverity } from "../../../../shared/types/repairs";

interface ReportDefectModalProps {
  onClose: () => void;
  onCreated: () => void;
}

interface FieldErrors {
  drone?: string;
  defect_type?: string;
  severity?: string;
  description?: string;
  detected_at?: string;
  form?: string;
}

export function ReportDefectModal({
  onClose,
  onCreated,
}: ReportDefectModalProps) {
  const { run } = useAbortableRequest();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [drone, setDrone] = useState("");
  const [defectType, setDefectType] = useState("");
  const [severity, setSeverity] = useState<DefectSeverity | "">("");
  const [description, setDescription] = useState("");
  const [detectedAt, setDetectedAt] = useState(
    toLocalDatetimeInput(),
  );
  const [errors, setErrors] = useState<FieldErrors>({});

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setErrors({});

    const droneId = Number(drone);
    if (!drone.trim() || Number.isNaN(droneId)) {
      setErrors({ drone: "Enter a valid drone ID." });
      return;
    }
    if (!defectType) {
      setErrors({ defect_type: "Select a defect type." });
      return;
    }
    if (!severity) {
      setErrors({ severity: "Select a severity level." });
      return;
    }
    if (description.trim().length < 10) {
      setErrors({
        description: "Description must be at least 10 characters.",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      await run(() =>
        createDefect({
          drone: droneId,
          defect_type: defectType,
          severity,
          description: description.trim(),
          detected_at: localDatetimeToIso(detectedAt),
        }),
      );
      onCreated();
      onClose();
    } catch (error) {
      if (isAbortError(error)) return;

      setErrors({
        drone: getApiFieldError(error, "drone"),
        defect_type: getApiFieldError(error, "defect_type"),
        severity: getApiFieldError(error, "severity"),
        description: getApiFieldError(error, "description"),
        detected_at: getApiFieldError(error, "detected_at"),
        form: getFormError(
          error,
          "Could not submit the defect report.",
        ),
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="Report Defect" onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            id="defect-drone"
            label="Drone"
            type="number"
            value={drone}
            onChange={setDrone}
            error={errors.drone}
            placeholder="Drone ID"
            isMono
          />

          <SelectField
            id="defect-severity"
            label="Severity"
            value={severity}
            onChange={(value) =>
              setSeverity(value as DefectSeverity | "")
            }
            error={errors.severity}
            options={SEVERITY_OPTIONS}
            placeholder="Select severity"
          />
        </div>

        <SelectField
          id="defect-type"
          label="Defect type"
          value={defectType}
          onChange={setDefectType}
          error={errors.defect_type}
          options={DEFECT_TYPE_OPTIONS}
          placeholder="Select type"
        />

        <TextField
          id="defect-detected-at"
          label="Detected at"
          type="datetime-local"
          value={detectedAt}
          onChange={setDetectedAt}
          error={errors.detected_at}
        />

        <TextAreaField
          id="defect-description"
          label="Description"
          value={description}
          onChange={setDescription}
          error={errors.description}
          rows={4}
          placeholder="Describe the defect in detail — conditions observed, flight data, symptoms..."
        />

        {errors.form ? (
          <p className="text-sm text-mc-error" role="alert">
            {errors.form}
          </p>
        ) : null}

        <ModalActions>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            icon={<Plus size={14} aria-hidden="true" />}
          >
            Submit Defect
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
