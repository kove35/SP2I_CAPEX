import React, { useState, useCallback } from 'react';
import {
  Card,
  Empty,
  Spin,
  Tag,
  Button,
  Space,
  Drawer,
  Form,
  Select,
  Input,
  DatePicker,
  message,
} from 'antd';

import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  LockOutlined,
  PlusOutlined,
} from '@ant-design/icons';

import dayjs from 'dayjs';
import { updateProjectExecutionAction } from '../../services/projectService';
import { compactSpatialLocation } from '../spatial/utils/spatialFormatters';
import './ActionsWorkflowBoard.css';

const STATUS_COLUMNS = [
  {
    key: 'TO_DO',
    label: 'À traiter',
    color: '#f5f5f5',
    icon: <PlusOutlined />,
  },
  {
    key: 'IN_PROGRESS',
    label: 'En cours',
    color: '#fffbe6',
    icon: <ClockCircleOutlined />,
  },
  {
    key: 'AT_RISK',
    label: 'À risque',
    color: '#fff1f0',
    icon: <WarningOutlined />,
  },
  {
    key: 'BLOCKED',
    label: 'Bloquée',
    color: '#fafafa',
    icon: <LockOutlined />,
  },
  {
    key: 'DONE',
    label: 'Terminée',
    color: '#f6ffed',
    icon: <CheckCircleOutlined />,
  },
];

const PRIORITY_COLORS = {
  CRITICAL: '#ff4d4f',
  HIGH: '#ff7a45',
  MEDIUM: '#faad14',
  LOW: '#1890ff',
};

const RISK_LEVEL_COLORS = {
  CRITICAL: '#ff4d4f',
  HIGH: '#ff7a45',
  MEDIUM: '#faad14',
  LOW: '#52c41a',
};

function ActionCard({ action, onDetails }) {
  const daysUntilDue = action.due_date
    ? dayjs(action.due_date).diff(dayjs(), 'days')
    : null;

  const isOverdue = daysUntilDue !== null && daysUntilDue < 0;
  const isUrgent = daysUntilDue !== null && daysUntilDue <= 3;
  const spatialLocation = compactSpatialLocation(action);

  return (
    <Card
      className="action-card"
      size="small"
      hoverable
      onClick={() => onDetails(action)}
      style={{
        borderLeft: `4px solid ${
          PRIORITY_COLORS[action.priority] || PRIORITY_COLORS.MEDIUM
        }`,
        opacity: action.status === 'DONE' ? 0.7 : 1,
        cursor: 'pointer',
      }}
    >
      <div className="action-card-header">
        <h4 className="action-title">{action.title}</h4>

        <Space size="small">
          <Tag color={PRIORITY_COLORS[action.priority]}>
            {action.priority}
          </Tag>

          {action.risk_level && (
            <Tag color={RISK_LEVEL_COLORS[action.risk_level]}>
              {action.risk_level}
            </Tag>
          )}
        </Space>
      </div>

      <p className="action-problem">{action.problem}</p>

      {spatialLocation ? (
        <div className="action-spatial-context">
          <span>Localisation</span>
          <strong>{spatialLocation}</strong>
        </div>
      ) : null}

      <div className="action-meta">
        <div className="meta-row">
          <span className="meta-label">Responsable :</span>

          <span className="meta-value">
            {action.responsible_name || action.responsible_role}
          </span>
        </div>

        {action.due_date && (
          <div className="meta-row">
            <span className="meta-label">Échéance :</span>

            <span
              className={`meta-value ${
                isOverdue ? 'overdue' : isUrgent ? 'urgent' : ''
              }`}
            >
              {dayjs(action.due_date).format('DD/MM/YYYY')}

              {daysUntilDue !== null && (
                <span className="days-info">
                  ({Math.abs(daysUntilDue)} jours)
                </span>
              )}
            </span>
          </div>
        )}

        {action.delivery_eta_days > 0 && (
          <div className="meta-row">
            <span className="meta-label">ETA :</span>

            <span className="meta-value">
              {Math.ceil(action.delivery_eta_days)} jours
            </span>
          </div>
        )}
      </div>

      <Button
        type="link"
        size="small"
        onClick={(e) => {
          e.stopPropagation();
          onDetails(action);
        }}
      >
        Détails →
      </Button>
    </Card>
  );
}

function ActionsWorkflowBoard({
  projectId,
  actions = [],
  onRefresh,
  loading = false,
}) {
  const [selectedAction, setSelectedAction] = useState(null);
  const [editForm] = Form.useForm();
  const [updating, setUpdating] = useState(false);

  const handleActionUpdate = useCallback(
    async (values) => {
      if (!selectedAction) return;

      setUpdating(true);

      try {
        const updates = {
          status: values.status,
          responsible_name: values.responsible_name,
          due_date: values.due_date
            ? values.due_date.format('YYYY-MM-DD')
            : null,
          recommended_action: values.recommended_action,
        };

        await updateProjectExecutionAction(
          projectId,
          selectedAction.id,
          updates
        );

        message.success('Action mise à jour avec succès');

        setSelectedAction(null);
        editForm.resetFields();

        onRefresh?.();
      } catch (error) {
        console.error('Update failed:', error);
        message.error('Erreur lors de la mise à jour');
      } finally {
        setUpdating(false);
      }
    },
    [selectedAction, projectId, onRefresh, editForm]
  );

  const renderColumn = (statusKey) => {
    const columnDef = STATUS_COLUMNS.find((c) => c.key === statusKey);

    if (!columnDef) return null;

    const columnActions = actions.filter(
      (a) => a.status === statusKey
    );

    return (
      <div
        key={statusKey}
        className="kanban-column"
        style={{
          backgroundColor: columnDef.color,
        }}
      >
        <div className="column-header">
          <Space size="small">
            {columnDef.icon}

            <span>{columnDef.label}</span>

            <Tag>{columnActions.length}</Tag>
          </Space>
        </div>

        <div className="column-content">
          {columnActions.length === 0 ? (
            <Empty
              description="Aucune action"
              style={{ marginTop: '20px' }}
            />
          ) : (
            columnActions.map((action) => (
              <ActionCard
                key={action.id}
                action={action}
                onDetails={setSelectedAction}
              />
            ))
          )}
        </div>
      </div>
    );
  };

  return (
    <Spin spinning={loading}>
      <div className="actions-workflow-board">
        <div className="kanban-container">
          {STATUS_COLUMNS.map((col) => renderColumn(col.key))}
        </div>

        <Drawer
          title={selectedAction?.title}
          placement="right"
          onClose={() => setSelectedAction(null)}
          open={!!selectedAction}
          width={500}
        >
          {selectedAction && (
            <Form
              form={editForm}
              layout="vertical"
              onFinish={handleActionUpdate}
              initialValues={{
                status: selectedAction.status,
                responsible_name:
                  selectedAction.responsible_name,
                due_date: selectedAction.due_date
                  ? dayjs(selectedAction.due_date)
                  : null,
                recommended_action:
                  selectedAction.recommended_action,
              }}
            >
              <Form.Item label="Titre">
                <Input
                  value={selectedAction.title}
                  disabled
                />
              </Form.Item>

              <Form.Item label="Problème">
                <Input.TextArea
                  value={selectedAction.problem}
                  disabled
                  rows={3}
                />
              </Form.Item>

              <Form.Item label="Impact">
                <Input.TextArea
                  value={selectedAction.impact}
                  disabled
                  rows={2}
                />
              </Form.Item>

              {compactSpatialLocation(selectedAction) ? (
                <div className="drawer-spatial-context">
                  <strong>Contexte spatial</strong>
                  <span>{compactSpatialLocation(selectedAction)}</span>
                  {selectedAction.ifc_guid || selectedAction.bim_object_id ? (
                    <small>
                      Objet BIM : {selectedAction.ifc_guid || selectedAction.bim_object_id}
                    </small>
                  ) : null}
                </div>
              ) : null}

              <Form.Item
                label="Statut"
                name="status"
                required
              >
                <Select
                  options={STATUS_COLUMNS.map((col) => ({
                    label: col.label,
                    value: col.key,
                  }))}
                />
              </Form.Item>

              <Form.Item
                label="Responsable"
                name="responsible_name"
              >
                <Input placeholder="Nom du responsable" />
              </Form.Item>

              <Form.Item
                label="Échéance"
                name="due_date"
              >
                <DatePicker format="DD/MM/YYYY" />
              </Form.Item>

              <Form.Item
                label="Action recommandée"
                name="recommended_action"
              >
                <Input.TextArea rows={3} />
              </Form.Item>

              <div className="drawer-meta">
                <div>
                  <strong>Priorité :</strong>{' '}
                  <Tag
                    color={
                      PRIORITY_COLORS[selectedAction.priority]
                    }
                  >
                    {selectedAction.priority}
                  </Tag>
                </div>

                {selectedAction.risk_level && (
                  <div>
                    <strong>Niveau risque :</strong>{' '}
                    <Tag
                      color={
                        RISK_LEVEL_COLORS[
                          selectedAction.risk_level
                        ]
                      }
                    >
                      {selectedAction.risk_level}
                    </Tag>
                  </div>
                )}

                {selectedAction.delivery_eta_days > 0 && (
                  <div>
                    <strong>ETA :</strong>{' '}
                    {Math.ceil(
                      selectedAction.delivery_eta_days
                    )}{' '}
                    jours
                  </div>
                )}

                {selectedAction.storage_impact > 0 && (
                  <div>
                    <strong>Impact stockage :</strong>{' '}
                    {selectedAction.storage_impact.toLocaleString(
                      'fr-FR'
                    )}{' '}
                    FCFA
                  </div>
                )}

                {selectedAction.criticality_score > 0 && (
                  <div>
                    <strong>Score critique :</strong>{' '}
                    {selectedAction.criticality_score.toFixed(1)}
                    /100
                  </div>
                )}
              </div>

              <Space style={{ marginTop: '20px' }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={updating}
                >
                  Enregistrer
                </Button>

                <Button
                  onClick={() => setSelectedAction(null)}
                >
                  Annuler
                </Button>
              </Space>
            </Form>
          )}
        </Drawer>
      </div>
    </Spin>
  );
}

export default ActionsWorkflowBoard;
