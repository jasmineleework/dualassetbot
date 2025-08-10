"""
AI-powered market analysis service using Claude API
Integrates with Anthropic Claude for intelligent market insights
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import anthropic
from loguru import logger
from dotenv import load_dotenv
from core.config import settings
import asyncio
from services.cache_service import cache_service

# Load environment variables
load_dotenv()

class AIAnalysisService:
    """Service for AI-powered market analysis using Claude"""
    
    def __init__(self):
        """Initialize AI Analysis Service with Claude"""
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('CLAUDE_MODEL', 'claude-3-opus-20240229')
        self.max_tokens = int(os.getenv('CLAUDE_MAX_TOKENS', '1500'))
        self.temperature = float(os.getenv('CLAUDE_TEMPERATURE', '0.7'))
        self.cache_ttl = int(os.getenv('AI_CACHE_TTL', '3600'))  # 1 hour default
        self.cache_enabled = os.getenv('AI_CACHE_ENABLED', 'true').lower() == 'true'
        self.enabled = bool(self.api_key)
        self.client = None  # Initialize to None first
        
        if self.enabled:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"AI Analysis Service initialized with Claude model: {self.model}")
                logger.info(f"Cache enabled: {self.cache_enabled}, TTL: {self.cache_ttl}s")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.enabled = False
                self.client = None
        else:
            logger.warning("AI Analysis Service disabled - no Anthropic API key configured")
    
    def _get_cache_key(self, symbol: str) -> str:
        """Generate cache key for AI analysis"""
        # Cache key includes symbol and current hour
        now = datetime.now()
        hour_key = now.strftime('%Y%m%d_%H')
        return f"ai_analysis:{symbol}:{hour_key}"
    
    async def analyze_market_with_ai(
        self, 
        symbol: str, 
        market_data: Dict[str, Any],
        kline_data: Optional[Dict[str, Any]] = None,
        dual_products: Optional[List[Dict[str, Any]]] = None,
        include_oi: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered market analysis using Claude
        
        Args:
            symbol: Trading pair symbol
            market_data: Current market data and indicators
            kline_data: Historical K-line data
            include_oi: Whether to include Open Interest analysis
            force_refresh: Force regenerate analysis even if cached
            
        Returns:
            AI-generated analysis and insights
        """
        if not self.enabled:
            return {
                'enabled': False,
                'message': 'AI analysis not available - API key not configured'
            }
        
        # Check cache if enabled and not forcing refresh
        cache_key = self._get_cache_key(symbol)
        if self.cache_enabled and not force_refresh:
            cached_analysis = cache_service.get(cache_key)
            if cached_analysis:
                logger.info(f"AI analysis cache hit for {symbol}")
                # Add cache metadata
                cached_analysis['from_cache'] = True
                cached_analysis['cache_timestamp'] = cached_analysis.get('timestamp', datetime.now().isoformat())
                return cached_analysis
        
        logger.info(f"Generating new AI analysis for {symbol} (force_refresh={force_refresh})")
        
        try:
            # Prepare context for AI
            context = self._prepare_market_context(symbol, market_data, kline_data)
            
            # Add dual products to context if available
            if dual_products:
                context['dual_products'] = dual_products
            
            # Generate prompts for different aspects
            prompts = self._create_analysis_prompts(context, include_oi, dual_products)
            
            # Get AI responses
            analyses = {}
            for aspect, prompt in prompts.items():
                try:
                    response = await self._get_ai_response(prompt)
                    analyses[aspect] = response
                except Exception as e:
                    logger.error(f"Failed to get AI response for {aspect}: {e}")
                    analyses[aspect] = f"Analysis unavailable: {str(e)}"
            
            # Combine analyses into comprehensive report
            result = self._format_ai_analysis(analyses, market_data)
            
            # Cache the result if caching is enabled
            if self.cache_enabled and result.get('enabled') and not result.get('error'):
                cache_service.set(cache_key, result, ttl=self.cache_ttl)
                logger.info(f"AI analysis cached for {symbol} with TTL={self.cache_ttl}s")
            
            # Add cache metadata
            result['from_cache'] = False
            result['generated_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed for {symbol}: {e}")
            return {
                'enabled': True,
                'error': str(e),
                'message': 'AI analysis temporarily unavailable',
                'from_cache': False
            }
    
    def _prepare_market_context(
        self, 
        symbol: str, 
        market_data: Dict[str, Any],
        kline_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare structured context for AI analysis"""
        
        context = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': market_data.get('current_price', 0),
            'price_change_24h': market_data.get('price_change_24h', 0),
            'volume_24h': market_data.get('volume_24h', 0),
            'trend': market_data.get('trend', {}),
            'signals': market_data.get('signals', {}),
            'volatility': market_data.get('volatility', {}),
            'support_resistance': market_data.get('support_resistance', {})
        }
        
        # Add technical indicators if available
        if 'signals' in market_data:
            context['technical_indicators'] = {
                'rsi': market_data['signals'].get('rsi_signal'),
                'macd': market_data['signals'].get('macd_signal'),
                'bollinger': market_data['signals'].get('bb_signal'),
                'recommendation': market_data['signals'].get('recommendation')
            }
        
        # Add K-line patterns if available
        if kline_data:
            context['kline_patterns'] = self._identify_patterns(kline_data)
        
        return context
    
    def _identify_patterns(self, kline_data: Dict[str, Any]) -> List[str]:
        """Identify common K-line patterns"""
        patterns = []
        
        # This is a simplified pattern recognition
        # In production, use proper technical analysis libraries
        if kline_data:
            # Example patterns (placeholder logic)
            patterns.append("Potential consolidation phase")
            
        return patterns
    
    def _create_analysis_prompts(
        self, 
        context: Dict[str, Any],
        include_oi: bool = False,
        dual_products: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, str]:
        """Create specific prompts for different analysis aspects"""
        
        prompts = {}
        
        # Market Overview Prompt
        prompts['market_overview'] = f"""
        As a professional cryptocurrency market analyst, analyze the current market conditions for {context['symbol']}.
        
        Current Data:
        - Price: ${context['current_price']:,.2f}
        - 24h Change: {context['price_change_24h']:.2f}%
        - 24h Volume: {context['volume_24h']:,.2f}
        - Trend: {context['trend'].get('trend', 'NEUTRAL')} ({context['trend'].get('strength', 'MODERATE')})
        - Volatility: {context['volatility'].get('risk_level', 'MEDIUM')}
        
        Technical Indicators:
        - RSI Signal: {context.get('technical_indicators', {}).get('rsi', 'NEUTRAL')}
        - MACD Signal: {context.get('technical_indicators', {}).get('macd', 'NEUTRAL')}
        - Overall Recommendation: {context.get('technical_indicators', {}).get('recommendation', 'HOLD')}
        
        Provide analysis including:
        1. Current market sentiment and trend analysis
        2. Key support levels (provide 2-3 specific price levels)
        3. Key resistance levels (provide 2-3 specific price levels)
        4. 24-hour price prediction (direction, target range, confidence level)
        5. Volume analysis insights
        
        Keep the response under 200 words. Please provide your response in Chinese (Simplified Chinese).
        """
        
        # K-line Pattern Analysis Prompt
        prompts['pattern_analysis'] = f"""
        Analyze the K-line chart patterns for {context['symbol']} based on recent price action.
        
        Current Price: ${context['current_price']:,.2f}
        Previous Support/Resistance (system calculated):
        - Support: ${context['support_resistance'].get('support', 0):,.2f}
        - Resistance: ${context['support_resistance'].get('resistance', 0):,.2f}
        
        Based on technical analysis, identify:
        1. More accurate support levels (2-3 levels)
        2. More accurate resistance levels (2-3 levels)
        3. Key chart patterns forming
        4. Potential breakout or breakdown levels
        5. Pattern reliability and timeframe
        
        Please provide your response in Chinese (Simplified Chinese). Keep under 150 words.
        """
        
        # Trading Strategy Prompt with actual dual products
        products_info = ""
        if dual_products:
            # Format BUY_LOW products
            buy_low_products = [p for p in dual_products if p.get('type') == 'BUY_LOW']
            sell_high_products = [p for p in dual_products if p.get('type') == 'SELL_HIGH']
            
            if buy_low_products:
                products_info += "\nActual BUY_LOW Products Available:\n"
                for p in buy_low_products[:3]:  # Show top 3
                    products_info += f"  - Product ID: {p.get('id')}\n"
                    products_info += f"    Strike Price: ${p.get('strike_price', 0):,.2f} ({(p.get('strike_price', 0) / context['current_price'] * 100):.1f}% of current)\n"
                    products_info += f"    APY: {p.get('apy', 0) * 100:.2f}%\n"
                    products_info += f"    Term: {p.get('term_days', 0)} days\n"
                    products_info += f"    Settlement Date: {p.get('settlement_date', 'N/A')}\n"
            
            if sell_high_products:
                products_info += "\nActual SELL_HIGH Products Available:\n"
                for p in sell_high_products[:3]:  # Show top 3
                    products_info += f"  - Product ID: {p.get('id')}\n"
                    products_info += f"    Strike Price: ${p.get('strike_price', 0):,.2f} ({(p.get('strike_price', 0) / context['current_price'] * 100):.1f}% of current)\n"
                    products_info += f"    APY: {p.get('apy', 0) * 100:.2f}%\n"
                    products_info += f"    Term: {p.get('term_days', 0)} days\n"
                    products_info += f"    Settlement Date: {p.get('settlement_date', 'N/A')}\n"
        
        prompts['trading_strategy'] = f"""
        Based on the current market analysis for {context['symbol']}, analyze these specific dual investment products and provide investment recommendations.
        
        Market Conditions:
        - Current Price: ${context['current_price']:,.2f}
        - Trend: {context['trend'].get('trend', 'NEUTRAL')}
        - Volatility: {context['volatility'].get('risk_level', 'MEDIUM')}
        - Technical Signal: {context.get('technical_indicators', {}).get('recommendation', 'HOLD')}
        {products_info if products_info else "No specific products available - provide general recommendations"}
        
        For each available product, analyze and recommend:
        1. Whether to invest (推荐/观望/不推荐)
        2. Confidence level (high/medium/low)
        3. Recommended position size (10%, 30%, 50%, or 70% of holdings)
        4. Exercise probability based on market analysis
        5. Key risk factors
        
        Specifically provide:
        1. For USDT holders (BUY_LOW products):
           - Which specific product ID to invest in (if any)
           - Position size recommendation
           - Confidence level and reasoning
        
        2. For {context['symbol'].replace("USDT", "")} holders (SELL_HIGH products):
           - Which specific product ID to invest in (if any)
           - Position size recommendation
           - Confidence level and reasoning
        
        3. Overall dual investment strategy for next 48 hours
        
        Please provide your response in Chinese (Simplified Chinese). Be specific with product IDs and percentages.
        """
        
        # Risk Assessment Prompt
        prompts['risk_assessment'] = f"""
        Perform a risk assessment for {context['symbol']} trading.
        
        Volatility Data:
        - ATR: {context['volatility'].get('atr', 0):.2f}
        - Volatility Ratio: {context['volatility'].get('volatility_ratio', 0):.4f}
        - Risk Level: {context['volatility'].get('risk_level', 'MEDIUM')}
        
        Identify:
        1. Main risk factors in current market
        2. Probability of significant price movement in next 24-48 hours
        3. Recommended position sizing for dual investment products
        4. Key risk events to monitor
        
        Please provide your response in Chinese (Simplified Chinese). Keep response under 100 words.
        """
        
        # Add Open Interest analysis if requested
        if include_oi:
            prompts['oi_analysis'] = f"""
            Analyze the Open Interest implications for {context['symbol']}.
            Note: Open Interest data is currently not available in the system.
            
            Provide general insights on:
            1. How OI changes typically affect price in current trend conditions
            2. What OI levels traders should monitor
            3. OI-based entry/exit signals
            Keep response under 100 words.
            """
        
        return prompts
    
    async def _get_ai_response(self, prompt: str) -> str:
        """Get response from Claude API"""
        try:
            # Use Claude API
            message = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system="You are a professional cryptocurrency market analyst with expertise in technical analysis, risk management, and dual investment products. Provide concise, actionable insights based on data.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text.strip()
            
        except anthropic.RateLimitError:
            logger.warning("Claude API rate limit reached")
            return "Analysis temporarily unavailable due to rate limiting. Please try again later."
        except anthropic.AuthenticationError:
            logger.error("Claude API authentication failed")
            return "AI analysis unavailable - authentication error"
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"AI analysis error: {str(e)}"
    
    def _format_ai_analysis(
        self, 
        analyses: Dict[str, str],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format AI analyses into structured response"""
        
        # Extract support/resistance from AI analysis
        support_resistance = self._extract_support_resistance(analyses.get('market_overview', ''))
        
        # Extract 24h prediction from AI analysis
        prediction_24h = self._extract_24h_prediction(analyses.get('market_overview', ''))
        
        # Extract dual investment recommendations
        dual_recommendations = self._extract_dual_recommendations(analyses.get('trading_strategy', ''))
        
        return {
            'enabled': True,
            'model': self.model,
            'timestamp': datetime.now().isoformat(),
            'market_overview': analyses.get('market_overview', ''),
            'pattern_analysis': analyses.get('pattern_analysis', ''),
            'trading_strategy': analyses.get('trading_strategy', ''),
            'risk_assessment': analyses.get('risk_assessment', ''),
            'oi_analysis': analyses.get('oi_analysis', ''),
            'confidence_score': self._calculate_confidence(analyses, market_data),
            'key_insights': self._extract_key_insights(analyses),
            'warnings': self._generate_warnings(market_data),
            'support_resistance': support_resistance,
            'prediction_24h': prediction_24h,
            'dual_recommendations': dual_recommendations
        }
    
    def _calculate_confidence(
        self, 
        analyses: Dict[str, str],
        market_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the analysis"""
        
        confidence = 0.5  # Base confidence
        
        # Adjust based on trend clarity
        trend = market_data.get('trend', {}).get('trend', 'NEUTRAL')
        if trend in ['BULLISH', 'BEARISH']:
            confidence += 0.1
        
        # Adjust based on signal consensus
        signals = market_data.get('signals', {})
        if all(s == signals.get('recommendation') for s in [
            signals.get('rsi_signal'),
            signals.get('macd_signal'),
            signals.get('bb_signal')
        ] if s):
            confidence += 0.15
        
        # Adjust based on AI response quality
        for analysis in analyses.values():
            if analysis and len(analysis) > 50 and 'error' not in analysis.lower():
                confidence += 0.05
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _extract_key_insights(self, analyses: Dict[str, str]) -> List[str]:
        """Extract key insights from AI analyses"""
        
        insights = []
        
        # Extract insights from each analysis
        for aspect, analysis in analyses.items():
            if analysis and len(analysis) > 20:
                # Simple extraction - in production, use NLP
                sentences = analysis.split('.')
                for sentence in sentences[:2]:  # Take first 2 sentences
                    if any(keyword in sentence.lower() for keyword in [
                        'recommend', 'suggest', 'likely', 'expect', 'potential',
                        'watch', 'consider', 'important', 'critical'
                    ]):
                        insights.append(sentence.strip())
        
        return insights[:5]  # Return top 5 insights
    
    def _generate_warnings(self, market_data: Dict[str, Any]) -> List[str]:
        """Generate risk warnings based on market conditions"""
        
        warnings = []
        
        # High volatility warning
        if market_data.get('volatility', {}).get('risk_level') == 'HIGH':
            warnings.append("High volatility detected - consider smaller position sizes")
        
        # Volume anomaly warning
        volume = market_data.get('volume_24h', 0)
        if volume == 0:
            warnings.append("Volume data unavailable - trade with caution")
        
        # Mixed signals warning
        signals = market_data.get('signals', {})
        signal_values = [
            signals.get('rsi_signal'),
            signals.get('macd_signal'),
            signals.get('bb_signal')
        ]
        if len(set(filter(None, signal_values))) > 2:
            warnings.append("Mixed technical signals - wait for clearer confirmation")
        
        return warnings
    
    def _extract_support_resistance(self, text: str) -> Dict[str, Any]:
        """Extract support and resistance levels from AI analysis text"""
        import re
        
        result = {
            'support_levels': [],
            'resistance_levels': [],
            'key_support': None,
            'key_resistance': None
        }
        
        try:
            # Try to extract prices mentioned as support/resistance
            # Look for patterns like "支撑位：$XXX" or "support at $XXX"
            support_pattern = r'(?:支撑|support)[^$]*?\$?([\d,]+\.?\d*)'
            resistance_pattern = r'(?:阻力|压力|resistance)[^$]*?\$?([\d,]+\.?\d*)'
            
            support_matches = re.findall(support_pattern, text, re.IGNORECASE)
            resistance_matches = re.findall(resistance_pattern, text, re.IGNORECASE)
            
            # Convert to float and clean up
            for match in support_matches[:3]:  # Take top 3
                try:
                    price = float(match.replace(',', ''))
                    result['support_levels'].append(price)
                except:
                    pass
            
            for match in resistance_matches[:3]:  # Take top 3
                try:
                    price = float(match.replace(',', ''))
                    result['resistance_levels'].append(price)
                except:
                    pass
            
            # Set key levels as the first ones found
            if result['support_levels']:
                result['key_support'] = result['support_levels'][0]
            if result['resistance_levels']:
                result['key_resistance'] = result['resistance_levels'][0]
                
        except Exception as e:
            logger.debug(f"Error extracting support/resistance: {e}")
        
        return result
    
    def _extract_24h_prediction(self, text: str) -> Dict[str, Any]:
        """Extract 24-hour price prediction from AI analysis"""
        
        result = {
            'direction': 'SIDEWAYS',
            'confidence': 0.5,
            'target_low': None,
            'target_high': None
        }
        
        try:
            # Detect direction from Chinese or English keywords
            if any(word in text for word in ['上涨', '看涨', 'bullish', 'upward', '上升']):
                result['direction'] = 'UP'
            elif any(word in text for word in ['下跌', '看跌', 'bearish', 'downward', '下降']):
                result['direction'] = 'DOWN'
            elif any(word in text for word in ['横盘', '震荡', 'sideways', 'consolidation', '盘整']):
                result['direction'] = 'SIDEWAYS'
            
            # Extract confidence if mentioned
            import re
            confidence_pattern = r'(\d+)%.*?(?:信心|confidence|概率|probability)'
            confidence_match = re.search(confidence_pattern, text, re.IGNORECASE)
            if confidence_match:
                result['confidence'] = float(confidence_match.group(1)) / 100
            
            # Extract target range if mentioned
            range_pattern = r'\$?([\d,]+\.?\d*)[^\d]*?[-到至]\s*\$?([\d,]+\.?\d*)'
            range_match = re.search(range_pattern, text)
            if range_match:
                try:
                    result['target_low'] = float(range_match.group(1).replace(',', ''))
                    result['target_high'] = float(range_match.group(2).replace(',', ''))
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"Error extracting 24h prediction: {e}")
        
        return result
    
    def _extract_dual_recommendations(self, text: str) -> Dict[str, Any]:
        """Extract dual investment recommendations from AI analysis"""
        import re
        
        result = {
            'buy_low_products': [],
            'sell_high_products': [],
            'usdt_strategy': {
                'recommend': False,
                'product_id': None,
                'position_size': 30,
                'confidence': 'medium',
                'reasoning': ''
            },
            'coin_strategy': {
                'recommend': False,
                'product_id': None,
                'position_size': 30,
                'confidence': 'medium',
                'reasoning': ''
            },
            'analysis_text': text  # Include full AI analysis text
        }
        
        try:
            # Extract product ID mentions
            product_id_pattern = r'(?:Product ID|产品ID|ID)[:\s]*([A-Z0-9\-]+)'
            product_ids = re.findall(product_id_pattern, text, re.IGNORECASE)
            
            # Extract recommendations for BUY_LOW
            if any(word in text for word in ['BUY_LOW', 'BUY LOW', '低买', 'BUYLOW']):
                buy_low_match = re.search(
                    r'BUY[_\s]?LOW.*?(?:推荐|建议|recommend).*?(\d+)%',
                    text, re.IGNORECASE | re.DOTALL
                )
                if buy_low_match:
                    result['usdt_strategy']['recommend'] = True
                    result['usdt_strategy']['position_size'] = int(buy_low_match.group(1))
                
                # Extract confidence
                if any(word in text for word in ['高置信', 'high confidence', '强烈推荐']):
                    result['usdt_strategy']['confidence'] = 'high'
                elif any(word in text for word in ['低置信', 'low confidence', '谨慎']):
                    result['usdt_strategy']['confidence'] = 'low'
                
                # Extract specific product ID for BUY_LOW
                for pid in product_ids:
                    if 'BUYLOW' in pid or 'BUY-LOW' in pid:
                        result['usdt_strategy']['product_id'] = pid
                        break
            
            # Extract recommendations for SELL_HIGH
            if any(word in text for word in ['SELL_HIGH', 'SELL HIGH', '高卖', 'SELLHIGH']):
                sell_high_match = re.search(
                    r'SELL[_\s]?HIGH.*?(?:推荐|建议|recommend).*?(\d+)%',
                    text, re.IGNORECASE | re.DOTALL
                )
                if sell_high_match:
                    result['coin_strategy']['recommend'] = True
                    result['coin_strategy']['position_size'] = int(sell_high_match.group(1))
                
                # Extract confidence
                if any(word in text for word in ['高置信', 'high confidence', '强烈推荐']):
                    result['coin_strategy']['confidence'] = 'high'
                elif any(word in text for word in ['低置信', 'low confidence', '谨慎']):
                    result['coin_strategy']['confidence'] = 'low'
                
                # Extract specific product ID for SELL_HIGH
                for pid in product_ids:
                    if 'SELLHIGH' in pid or 'SELL-HIGH' in pid:
                        result['coin_strategy']['product_id'] = pid
                        break
            
            # Parse product recommendations from structured text
            # Look for patterns like "产品ID: XXX ... 推荐/观望/不推荐"
            product_blocks = re.findall(
                r'Product ID[:\s]*([^\n]+).*?(?:推荐|观望|不推荐)',
                text, re.IGNORECASE | re.DOTALL
            )
            
            for block in product_blocks:
                if 'BUYLOW' in block or 'BUY-LOW' in block:
                    recommendation = '推荐' if '推荐' in block and '不推荐' not in block else '观望'
                    result['buy_low_products'].append({
                        'product_id': block.strip(),
                        'recommendation': recommendation,
                        'confidence': result['usdt_strategy']['confidence']
                    })
                elif 'SELLHIGH' in block or 'SELL-HIGH' in block:
                    recommendation = '推荐' if '推荐' in block and '不推荐' not in block else '观望'
                    result['sell_high_products'].append({
                        'product_id': block.strip(),
                        'recommendation': recommendation,
                        'confidence': result['coin_strategy']['confidence']
                    })
                    
        except Exception as e:
            logger.debug(f"Error extracting dual recommendations: {e}")
        
        return result
    
    async def generate_trade_rationale(
        self,
        product: Dict[str, Any],
        market_data: Dict[str, Any],
        decision: str
    ) -> str:
        """Generate AI explanation for a trading decision"""
        
        if not self.enabled:
            return "AI rationale not available"
        
        prompt = f"""
        Explain the rationale for {decision} the following dual investment product:
        
        Product: {product.get('type')} for {product.get('asset')}
        Strike Price: ${product.get('strike_price', 0):,.2f}
        Current Price: ${market_data.get('current_price', 0):,.2f}
        APY: {product.get('apy', 0)*100:.1f}%
        Market Trend: {market_data.get('trend', {}).get('trend', 'NEUTRAL')}
        
        Provide a concise explanation (50 words max) covering:
        1. Why this product fits current market conditions
        2. Risk-reward assessment
        3. Expected outcome
        """
        
        try:
            response = await self._get_ai_response(prompt)
            return response
        except Exception as e:
            logger.error(f"Failed to generate trade rationale: {e}")
            return "Unable to generate AI rationale"

# Create singleton instance
ai_analysis_service = AIAnalysisService()