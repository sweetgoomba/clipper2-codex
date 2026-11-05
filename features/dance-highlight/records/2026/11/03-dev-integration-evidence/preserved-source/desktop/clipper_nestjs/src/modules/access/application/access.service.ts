import {
  BadGatewayException,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import type { AuthContext } from '../../../core/auth/auth-context.service';
import { WebApiClient } from '../../../core/web-api/web-api-client.service';
import {
  responseArray,
  responseEnum,
  responseRecord,
  responseString,
} from '../../../core/web-api/web-api-response.projector';

export type CreditSource =
  | 'subscription'
  | 'admin_plan'
  | 'topup'
  | 'admin_adjustment'
  | 'promotion'
  | 'free_trial';

export interface CurrentAccessView {
  access: {
    source: 'free' | 'free_trial' | 'subscription' | 'admin_plan' | 'promotion';
    tierId: string;
    tierCode: string;
    tierName: string;
    entitlementMode: 'allowlist' | 'all';
    allowedPluginKeys: string[];
    spendableCreditSources: CreditSource[];
  } | null;
}

const ACCESS_SOURCES = ['free', 'free_trial', 'subscription', 'admin_plan', 'promotion'] as const;
const ENTITLEMENT_MODES = ['allowlist', 'all'] as const;
export const CREDIT_SOURCES = [
  'subscription',
  'admin_plan',
  'topup',
  'admin_adjustment',
  'promotion',
  'free_trial',
] as const satisfies readonly CreditSource[];

@Injectable()
export class AccessService {
  constructor(private readonly webApi: WebApiClient) {}

  async current(auth: Pick<AuthContext, 'accessToken'>): Promise<CurrentAccessView> {
    const response = await this.webApi.getJson<unknown>('/access/current', {
      bearerToken: this.requireBearer(auth),
    });
    try {
      const root = responseRecord(response);
      if (root.access === null) return { access: null };
      const access = responseRecord(root.access);
      return {
        access: {
          source: responseEnum(access.source, ACCESS_SOURCES),
          tierId: responseString(access.tierId),
          tierCode: responseString(access.tierCode),
          tierName: responseString(access.tierName),
          entitlementMode: responseEnum(
            access.entitlementMode,
            ENTITLEMENT_MODES,
          ),
          allowedPluginKeys: responseArray(access.allowedPluginKeys).map(
            responseString,
          ),
          spendableCreditSources: responseArray(
            access.spendableCreditSources,
          ).map((source) => responseEnum(source, CREDIT_SOURCES)),
        },
      };
    } catch {
      throw new BadGatewayException('Web API access response is invalid.');
    }
  }

  private requireBearer(auth: Pick<AuthContext, 'accessToken'>): string {
    const bearerToken = auth.accessToken?.trim();
    if (!bearerToken) {
      throw new UnauthorizedException('user authentication is required for access summary');
    }
    return bearerToken;
  }
}
