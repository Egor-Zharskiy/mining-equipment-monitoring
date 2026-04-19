import { Suspense, lazy } from 'react'
import { Navigate, createBrowserRouter } from 'react-router-dom'
import { ProtectedRoute } from '../auth/ProtectedRoute'
import { LoadingScreen } from '../components/LoadingScreen'
import { HomeRedirect } from './HomeRedirect'

function lazyPage(loader, exportName) {
  return lazy(() => loader().then((module) => ({ default: module[exportName] })))
}

function renderLazyPage(Component, label) {
  return (
    <Suspense fallback={<LoadingScreen label={label} />}>
      <Component />
    </Suspense>
  )
}

const AppShell = lazyPage(() => import('../layout/AppShell'), 'AppShell')
const AuditLogsPage = lazyPage(() => import('../pages/AuditLogsPage'), 'AuditLogsPage')
const DashboardPage = lazyPage(() => import('../pages/DashboardPage'), 'DashboardPage')
const EquipmentDetailsPage = lazyPage(
  () => import('../pages/EquipmentDetailsPage'),
  'EquipmentDetailsPage',
)
const EquipmentListPage = lazyPage(() => import('../pages/EquipmentListPage'), 'EquipmentListPage')
const EventsPage = lazyPage(() => import('../pages/EventsPage'), 'EventsPage')
const LoginPage = lazyPage(() => import('../pages/LoginPage'), 'LoginPage')
const MonitoringCatalogsPage = lazyPage(
  () => import('../pages/MonitoringCatalogsPage'),
  'MonitoringCatalogsPage',
)
const MaintenanceTasksPage = lazyPage(
  () => import('../pages/MaintenanceTasksPage'),
  'MaintenanceTasksPage',
)
const MaintenanceRecordsPage = lazyPage(
  () => import('../pages/MaintenanceRecordsPage'),
  'MaintenanceRecordsPage',
)
const MaintenancePlansPage = lazyPage(
  () => import('../pages/MaintenancePlansPage'),
  'MaintenancePlansPage',
)
const NotificationsPage = lazyPage(() => import('../pages/NotificationsPage'), 'NotificationsPage')
const RolesPage = lazyPage(() => import('../pages/RolesPage'), 'RolesPage')
const ThresholdRulesPage = lazyPage(
  () => import('../pages/ThresholdRulesPage'),
  'ThresholdRulesPage',
)
const UsersPage = lazyPage(() => import('../pages/UsersPage'), 'UsersPage')

export const router = createBrowserRouter([
  {
    path: '/login',
    element: renderLazyPage(LoginPage, 'Загрузка формы входа'),
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        {renderLazyPage(AppShell, 'Загрузка рабочей области')}
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <HomeRedirect />,
      },
      {
        path: 'dashboard',
        element: (
          <ProtectedRoute requiredPermissions={['analytics.read']}>
            {renderLazyPage(DashboardPage, 'Загрузка панели мониторинга')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'equipment',
        element: (
          <ProtectedRoute requiredPermissions={['equipment.read']}>
            {renderLazyPage(EquipmentListPage, 'Загрузка списка оборудования')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'equipment/:equipmentId',
        element: (
          <ProtectedRoute requiredPermissions={['equipment.read']}>
            {renderLazyPage(EquipmentDetailsPage, 'Загрузка карточки оборудования')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'events',
        element: (
          <ProtectedRoute requiredPermissions={['events.read']}>
            {renderLazyPage(EventsPage, 'Загрузка журнала событий')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'maintenance',
        element: (
          <ProtectedRoute requiredPermissions={['maintenance.read']}>
            {renderLazyPage(MaintenanceTasksPage, 'Загрузка задач технического обслуживания')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'maintenance-records',
        element: (
          <ProtectedRoute requiredPermissions={['maintenance.read']}>
            {renderLazyPage(MaintenanceRecordsPage, 'Загрузка истории технического обслуживания')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'maintenance-plans',
        element: (
          <ProtectedRoute requiredPermissions={['maintenance.read']}>
            {renderLazyPage(MaintenancePlansPage, 'Загрузка планов технического обслуживания')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'notifications',
        element: (
          <ProtectedRoute requiredPermissions={['notifications.read']}>
            {renderLazyPage(NotificationsPage, 'Загрузка уведомлений')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/users',
        element: (
          <ProtectedRoute requiredPermissions={['users.read']}>
            {renderLazyPage(UsersPage, 'Загрузка управления пользователями')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/roles',
        element: (
          <ProtectedRoute requiredPermissions={['roles.read']}>
            {renderLazyPage(RolesPage, 'Загрузка ролей и прав')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/catalogs',
        element: (
          <ProtectedRoute requiredPermissions={['equipment.read']}>
            {renderLazyPage(MonitoringCatalogsPage, 'Загрузка справочников мониторинга')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/audit-logs',
        element: (
          <ProtectedRoute requiredPermissions={['audit.read']}>
            {renderLazyPage(AuditLogsPage, 'Загрузка журнала аудита')}
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin/threshold-rules',
        element: (
          <ProtectedRoute requiredPermissions={['threshold_rules.read']}>
            {renderLazyPage(ThresholdRulesPage, 'Загрузка пороговых правил')}
          </ProtectedRoute>
        ),
      },
    ],
  },
  {
    path: '*',
    element: <Navigate replace to="/" />,
  },
])
