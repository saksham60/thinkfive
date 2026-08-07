import { BankingMCPServer } from './bankingMcp';
import { FraudMCPServer } from './fraudMcp';
import { CaseMCPServer } from './caseMcp';
import { db } from '../db';

export class MCPGateway {
  private static idempotencyCache = new Set<string>();

  public static async executeTool(
    serverName: string,
    toolName: string,
    args: any,
    context: { userRole?: string; customerId?: string; idempotencyKey?: string }
  ): Promise<any> {
    // 1. Check Idempotency Key
    if (context.idempotencyKey) {
      if (this.idempotencyCache.has(context.idempotencyKey)) {
        return {
          status: 'IDEMPOTENT_REPLAY',
          message: 'Operation already executed with this idempotency key.',
          idempotencyKey: context.idempotencyKey
        };
      }
      this.idempotencyCache.add(context.idempotencyKey);
    }

    // 2. Permission & Ownership Verification
    if (context.customerId && args.customerId && args.customerId !== context.customerId && context.userRole === 'customer') {
      db.addAuditEvent(
        'MCPGateway',
        context.userRole || 'customer',
        `DENIED_ACCESS:${toolName}`,
        `Customer ${context.customerId} attempted unauthorized tool access on customer ${args.customerId}`,
        true,
        'denied',
        serverName
      );
      throw new Error(`Security Violation: Customer ${context.customerId} is not authorized to access resources belonging to ${args.customerId}`);
    }

    // 3. Dispatch to MCP Servers
    switch (serverName) {
      case BankingMCPServer.SERVER_NAME:
      case 'BankingMCP':
        switch (toolName) {
          case 'get_customer_profile':
            return BankingMCPServer.getCustomerProfile({ ...args, userRole: context.userRole });
          case 'get_account_summary':
            return BankingMCPServer.getAccountSummary({ ...args, userRole: context.userRole });
          case 'get_transaction':
            return BankingMCPServer.getTransaction({ ...args, userRole: context.userRole });
          case 'get_recent_transactions':
            return BankingMCPServer.getRecentTransactions({ ...args, userRole: context.userRole });
          case 'get_card_status':
            return BankingMCPServer.getCardStatus({ ...args, userRole: context.userRole });
          case 'freeze_card':
            return BankingMCPServer.freezeCard({ ...args, userRole: context.userRole });
          default:
            throw new Error(`Unknown Banking MCP Tool: ${toolName}`);
        }

      case FraudMCPServer.SERVER_NAME:
      case 'FraudMCP':
        switch (toolName) {
          case 'get_active_alerts':
            return FraudMCPServer.getActiveAlerts({ ...args, userRole: context.userRole });
          case 'calculate_fraud_score':
            return FraudMCPServer.calculateFraudScore({ ...args, userRole: context.userRole });
          case 'get_device_risk':
            return FraudMCPServer.getDeviceRisk({ ...args, userRole: context.userRole });
          case 'get_related_entities':
            return FraudMCPServer.getRelatedEntities({ ...args, userRole: context.userRole });
          case 'get_customer_risk_profile':
            return FraudMCPServer.getCustomerRiskProfile({ ...args, userRole: context.userRole });
          case 'get_fraud_evidence':
            return FraudMCPServer.getFraudEvidence({ ...args, userRole: context.userRole });
          default:
            throw new Error(`Unknown Fraud MCP Tool: ${toolName}`);
        }

      case CaseMCPServer.SERVER_NAME:
      case 'CaseMCP':
        switch (toolName) {
          case 'create_case':
            return CaseMCPServer.createCase({ ...args, userRole: context.userRole });
          case 'update_case':
            return CaseMCPServer.updateCase({ ...args, userRole: context.userRole });
          case 'assign_case':
            return CaseMCPServer.assignCase({ ...args, userRole: context.userRole });
          case 'add_case_note':
            return CaseMCPServer.addCaseNote({ ...args, userRole: context.userRole });
          case 'request_approval':
            return CaseMCPServer.requestApproval({ ...args, userRole: context.userRole });
          case 'send_customer_notification':
            return CaseMCPServer.sendCustomerNotification({ ...args, userRole: context.userRole });
          default:
            throw new Error(`Unknown Case MCP Tool: ${toolName}`);
        }

      default:
        throw new Error(`Unknown MCP Server: ${serverName}`);
    }
  }
}
