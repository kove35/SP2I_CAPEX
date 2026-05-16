import { request } from "./apiClient";

function buildExcelFormData(file) {
  const formData = new FormData();
  formData.append("fichier", file);
  return formData;
}

export async function analyzeExcel(file) {
  return request({
    url: "/api/upload/excel",
    method: "POST",
    data: buildExcelFormData(file),
  });
}

export async function syncExcel(file) {
  return request({
    url: "/api/upload/excel/sync",
    method: "POST",
    data: buildExcelFormData(file),
  });
}

export async function validateAiMapping(fileId, mapping) {
  return request({
    url: `/dqe/validate-mapping/${fileId}`,
    method: "POST",
    data: mapping,
  });
}
