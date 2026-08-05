import { useState } from "react";
import type { FormEvent } from "react";
import { Plus } from "lucide-react";

import { Button } from "../../../admin/components/Button";
import { Modal } from "../../../admin/components/Modal";
import { ModalActions } from "../../../admin/components/ModalActions";
import {
  TextAreaField,
  TextField,
} from "../../../admin/components/FormFields";
import { createRepairOrder } from "../../api/repairsApi";
import { isAbortError } from "../../../../shared/api/apiClient";
import {
  getApiFieldError,
  getFormError,
} from "../../../../shared/utils/apiErrors";
import { useAbortableRequest } from "../../../../shared/hooks/useAbortableRequest";

interface NewRepairOrderModalProps {
  onClose: () => void;
  onCreated: () => void;
}

interface FieldErrors {
  drone?: string;
  defect_report?: string;
  assigned_to?: string;
  description?: string;
  form?: string;
}

export function NewRepairOrderModal({
  onClose,
  onCreated,
}: NewRepairOrderModalProps) {
  const { run } = useAbortableRequest();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [drone, setDrone] = useState("");
  const [defectReport, setDefectReport] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setErrors({});

    const droneId = Number(drone);
    if (!drone.trim() || Number.isNaN(droneId)) {
      setErrors({ drone: "Enter a valid drone ID." });
      return;
    }
    if (description.trim().length < 10) {
      setErrors({
        description: "Description must be at least 10 characters.",
      });
      return;
    }

    const defectId = defectReport.trim()
      ? Number(defectReport)
      : null;
    if (defectReport.trim() && Number.isNaN(defectId)) {
      setErrors({
        defect_report: "Enter a valid defect ID or leave empty.",
      });
      return;
    }

    const assignee = assignedTo.trim()
      ? Number(assignedTo)
      : null;
    if (assignedTo.trim() && Number.isNaN(assignee)) {
      setErrors({
        assigned_to: "Enter a valid user ID or leave empty.",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      await run(() =>
        createRepairOrder({
          drone: droneId,
          defect_report: defectId,
          description: description.trim(),
          assigned_to: assignee,
        }),
      );
      onCreated();
      onClose();
    } catch (error) {
      if (isAbortError(error)) return;

      setErrors({
        drone: getApiFieldError(error, "drone"),
        defect_report: getApiFieldError(error, "defect_report"),
        assigned_to: getApiFieldError(error, "assigned_to"),
        description: getApiFieldError(error, "description"),
        form: getFormError(
          error,
          "Could not create the repair order.",
        ),
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="New Repair Order" onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            id="order-drone"
            label="Drone"
            type="number"
            value={drone}
            onChange={setDrone}
            error={errors.drone}
            placeholder="Drone ID"
            isMono
          />

          <TextField
            id="order-defect"
            label="Linked defect"
            type="number"
            value={defectReport}
            onChange={setDefectReport}
            error={errors.defect_report}
            placeholder="Optional defect ID"
            isMono
          />
        </div>

        <TextField
          id="order-assignee"
          label="Assign to"
          type="number"
          value={assignedTo}
          onChange={setAssignedTo}
          error={errors.assigned_to}
          placeholder="Optional user ID"
          isMono
        />

        <TextAreaField
          id="order-description"
          label="Notes"
          value={description}
          onChange={setDescription}
          error={errors.description}
          rows={4}
          placeholder="Work scope, parts needed, constraints..."
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
            Create Order
          </Button>
        </ModalActions>
      </form>
    </Modal>
  );
}
