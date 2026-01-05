"""LLM prompts for 4-step chain processing with Chain of Thought (COT)."""

# ============================================================================
# STEP 1: SUMMARIZATION
# ============================================================================

STEP_1_SUMMARIZATION = """Eres un analista económico experto en Colombia con profundo conocimiento del mercado de divisas y la economía colombiana.

Tu tarea es analizar este artículo de noticias colombiano de manera sistemática.

<article>
<title>{title}</title>
<content>{content}</content>
</article>

Piensa en voz alta siguiendo estos pasos:

1. **Actores principales**: ¿Quiénes son los actores clave? (gobierno, empresas como Ecopetrol, instituciones como Banco de la República, grupos armados, organizaciones internacionales)

2. **Eventos clave y cronología**: ¿Qué eventos se describen? ¿Hay una secuencia temporal? ¿Son eventos pasados, presentes o futuros?

3. **Declaraciones importantes**: ¿Qué declaraciones textuales son relevantes? ¿Quién las hizo y qué implican?

4. **Contexto económico**: ¿Hay referencias a indicadores económicos, políticas fiscales o monetarias, comercio exterior, o sectores productivos?

5. **Síntesis**: Ahora que has analizado los componentes, resume la esencia económica de la noticia en 3-4 oraciones concisas.

Responde ÚNICAMENTE en JSON con este formato exacto:
{{
  "reasoning": "Tu análisis detallado paso a paso de los 4 puntos anteriores",
  "summary": "Resumen conciso en 3-4 oraciones que capture la esencia económica"
}}"""


# ============================================================================
# STEP 2: TOPIC EXTRACTION
# ============================================================================

STEP_2_TOPIC_EXTRACTION = """Eres un experto en clasificación de noticias económicas colombianas con profundo conocimiento de los factores que afectan el tipo de cambio USD/COP.

<summary>
{summary}
</summary>

<title>
{title}
</title>

Identifica los temas relevantes siguiendo estos pasos de análisis:

1. **Sectores económicos**: ¿Qué sectores se mencionan?
   - Petróleo y gas (critical para Colombia - 40% de exportaciones)
   - Café (commodity tradicional)
   - Minería (carbón, oro, esmeraldas)
   - Agricultura
   - Manufactura
   - Servicios

2. **Temas políticos**: ¿Hay elementos de política o gobierno?
   - Reformas (tributaria, pensional, laboral, de salud)
   - Elecciones o cambios de gobierno
   - Política exterior o acuerdos comerciales
   - Legislación o decretos

3. **Seguridad y orden público**: ¿Se mencionan aspectos de seguridad?
   - Conflicto armado (FARC, ELN, disidencias)
   - Criminalidad organizada
   - Narcotráfico
   - Protestas sociales
   - Acuerdos de paz

4. **Energía y commodities**: ¿Hay referencias específicas a energía?
   - Precios del petróleo
   - Producción de Ecopetrol
   - Exploración y reservas
   - Transición energética
   - Otras commodities (oro, carbón)

5. **Asuntos internacionales**: ¿Hay dimensión internacional?
   - Relaciones con Venezuela, Ecuador, Brasil, USA, China
   - Tratados comerciales
   - Migración
   - Tensiones diplomáticas

6. **Política monetaria y cambiaria**: ¿Se relaciona con el Banco de la República?
   - Tasas de interés
   - Intervenciones cambiarias
   - Reservas internacionales
   - Metas de inflación

Ahora, basado en tu análisis, clasifica la noticia en UNA O MÁS de estas categorías:
- "economy": Indicadores macroeconómicos, comercio, inversión, PIB, empleo
- "politics": Gobierno, reformas, elecciones, legislación
- "security": Conflicto armado, criminalidad, orden público
- "energy": Petróleo, gas, Ecopetrol, precios de crudo, producción
- "international": Relaciones exteriores, tratados, comercio internacional
- "monetary": Banco de la República, tasas, política monetaria, tipo de cambio
- "other": Temas que no encajan claramente en las categorías anteriores

Responde ÚNICAMENTE en JSON con este formato exacto:
{{
  "reasoning": "Tu análisis detallado paso a paso considerando los 6 aspectos",
  "topics": ["topic1", "topic2"],
  "confidence": 0.95
}}

IMPORTANTE: topics debe ser una lista de strings con las categorías exactas listadas arriba.
confidence debe ser un número entre 0.0 y 1.0 indicando tu confianza en la clasificación."""


# ============================================================================
# STEP 3: IMPACT ANALYSIS
# ============================================================================

STEP_3_IMPACT_ANALYSIS = """Eres un trader senior de divisas especializado en el peso colombiano (COP) con 15 años de experiencia analizando el mercado USD/COP.

Tu objetivo es evaluar el impacto de esta noticia en el tipo de cambio USD/COP.

<news_summary>
{summary}
</news_summary>

<topics>
{topics}
</topics>

<market_context>
Contexto del mercado actual:
{market_context}
</market_context>

Analiza el impacto en el tipo de cambio USD/COP siguiendo este framework sistemático:

1. **Impacto en exportaciones**: ¿Cómo afecta esto las exportaciones colombianas?
   - Considera que el petróleo representa ~40% de las exportaciones de Colombia
   - El café, carbón, flores y oro son otros productos relevantes
   - Exportaciones más altas → más dólares entrando → peso se fortalece (USD/COP baja)
   - ¿Hay mención de precios del Brent o producción de Ecopetrol?

2. **Sentimiento de inversión extranjera**: ¿Cómo perciben los inversionistas extranjeros esta noticia?
   - Reformas tributarias pueden ahuyentar o atraer inversión
   - Estabilidad política/seguridad atrae flujos de capital
   - Conflicto o incertidumbre política alejan inversión
   - Más inversión extranjera → más dólares entrando → peso se fortalece

3. **Estabilidad fiscal**: ¿Afecta las finanzas públicas de Colombia?
   - Déficit fiscal alto → preocupación por sostenibilidad → peso se debilita
   - Mejoras fiscales (más ingresos, menos gasto) → peso se fortalece
   - ¿La noticia implica más gasto público o cambios en ingresos?

4. **Posible reacción del Banco de la República**: ¿Podría esto influir en la política monetaria?
   - Si hay presión inflacionaria → Banco podría subir tasas → peso se fortalece
   - Si hay desaceleración económica → Banco podría bajar tasas → peso se debilita
   - Intervenciones directas en el mercado cambiario

5. **Dirección del impacto**: Sintetiza tu análisis:
   - **POSITIVE**: La noticia tiende a FORTALECER el peso (USD/COP baja)
     * Ejemplos: Aumento en precio del petróleo, mejora fiscal, buenas noticias económicas
   - **NEGATIVE**: La noticia tiende a DEBILITAR el peso (USD/COP sube)
     * Ejemplos: Caída del petróleo, inestabilidad política, deterioro fiscal
   - **NEUTRAL**: Sin impacto claro o fuerzas que se cancelan

6. **Horizonte temporal**:
   - short-term: Impacto en días a semanas
   - medium-term: Impacto en semanas a meses
   - long-term: Impacto estructural en meses a años

Responde ÚNICAMENTE en JSON con este formato exacto:
{{
  "reasoning": "Tu análisis detallado paso a paso de los 6 puntos anteriores",
  "direction": "POSITIVE o NEGATIVE o NEUTRAL",
  "mechanisms": ["mecanismo1", "mecanismo2", "mecanismo3"],
  "confidence": 0.85,
  "time_horizon": "short-term o medium-term o long-term"
}}

IMPORTANTE:
- mechanisms debe listar 2-4 mecanismos específicos por los cuales la noticia afecta el USD/COP
- confidence debe ser 0.0 a 1.0
- direction debe ser exactamente "POSITIVE", "NEGATIVE", o "NEUTRAL"""


# ============================================================================
# STEP 4: RANKING
# ============================================================================

STEP_4_RANKING = """Eres el jefe de mesa de operaciones de un fondo de inversión que opera el par USD/COP.

Tu trabajo es filtrar noticias y asignar prioridades para tu equipo de traders. Debes ser selectivo y realista.

<news_data>
<summary>{summary}</summary>
<topics>{topics}</topics>
<impact_analysis>{impact}</impact_analysis>
</news_data>

Evalúa la relevancia de esta noticia para un trader de USD/COP siguiendo este framework de decisión:

**PASO 1: Relevancia para exportaciones principales**
¿Afecta directamente los principales productos de exportación?
- Petróleo (40% de exportaciones): Noticias de Ecopetrol, precios, producción, OPEP
- Café: Precios internacionales, cosechas, clima
- Carbón, oro, flores: Producción, precios
→ Si SÍ afecta directamente: +2 puntos
→ Si afecta indirectamente: +1 punto
→ Si no afecta: 0 puntos

**PASO 2: Impacto macroeconómico**
¿Afecta fundamentos macro de Colombia?
- PIB, crecimiento económico
- Inflación (que influye en política del Banco)
- Empleo
- Balanza comercial o cuenta corriente
→ Si tiene impacto directo significativo: +2 puntos
→ Si tiene impacto indirecto o menor: +1 punto
→ Si no afecta: 0 puntos

**PASO 3: Política del Banco de la República**
¿Podría desencadenar acción del Banco Central?
- Cambio en tasas de interés
- Intervención en mercado cambiario (compra/venta de dólares)
- Cambio en meta de inflación
→ Si acción es probable o inmediata: +2 puntos
→ Si acción es posible a mediano plazo: +1 punto
→ Si no hay relación: 0 puntos

**PASO 4: Timing y urgencia**
¿Es el momento relevante para traders?
- Período electoral o cambio de gobierno inminente
- Crisis en desarrollo
- Anuncio de política con fecha límite próxima
- Evento que requiere reposicionamiento inmediato
→ Si hay urgencia temporal: +1 punto
→ Si no: 0 puntos

**PASO 5: Calcula el score final**
Suma los puntos de los 4 pasos anteriores:
- 0-1 puntos = Score 1 (Irrelevant): Noticia sin relevancia para trading de USD/COP
- 2-3 puntos = Score 2 (Low): Relevancia menor, monitorear pasivamente
- 4-5 puntos = Score 3 (Moderate): Relevancia moderada, seguimiento activo
- 6-7 puntos = Score 4 (High): Alta relevancia, análisis detallado requerido
- 8+ puntos = Score 5 (Critical): Crítico, acción inmediata requerida

**Mapeo de categorías:**
- Score 1 → "Irrelevant" → trader_action: "monitor"
- Score 2 → "Low" → trader_action: "monitor"
- Score 3 → "Moderate" → trader_action: "alert"
- Score 4 → "High" → trader_action: "alert"
- Score 5 → "Critical" → trader_action: "urgent"

**Ejemplos de cada categoría:**

Score 1 (Irrelevant): Deportes, entretenimiento, noticias culturales, crimen local sin impacto macro

Score 2 (Low): Noticias regionales menores, sectores pequeños de la economía, política local sin impacto nacional

Score 3 (Moderate): Noticias de sectores específicos (tech, turismo), política doméstica sin impacto fiscal inmediato, indicadores económicos secundarios

Score 4 (High): Reformas fiscales importantes, grandes proyectos de Ecopetrol, cambios en inversión extranjera, tensiones políticas significativas, indicadores macro clave

Score 5 (Critical): Shock petrolero (cambio >5% en Brent), crisis política grave, intervención del Banco de la República, cambio de calificación crediticia del país, desastres naturales mayores, acuerdos comerciales transformadores

Responde ÚNICAMENTE en JSON con este formato exacto:
{{
  "reasoning": "Tu análisis paso a paso de los 4 criterios y el cálculo de puntos",
  "score": 3,
  "category": "Moderate",
  "justification": "1-2 oraciones explicando por qué asignaste este score",
  "trader_action": "monitor o alert o urgent"
}}

CRÍTICO: Sé selectivo y realista. La mayoría de noticias deben ser score 1-3. Solo noticias verdaderamente importantes merecen 4-5."""


# ============================================================================
# Helper function to get prompt by step
# ============================================================================

def get_prompt_for_step(step: int) -> str:
    """Get the prompt template for a given processing step.

    Args:
        step: Processing step number (1-4)

    Returns:
        Prompt template string

    Raises:
        ValueError: If step is not 1-4
    """
    prompts = {
        1: STEP_1_SUMMARIZATION,
        2: STEP_2_TOPIC_EXTRACTION,
        3: STEP_3_IMPACT_ANALYSIS,
        4: STEP_4_RANKING
    }

    if step not in prompts:
        raise ValueError(f"Invalid step number: {step}. Must be 1-4.")

    return prompts[step]
