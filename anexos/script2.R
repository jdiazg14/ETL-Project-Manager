# El código siguiente, que crea un dataframe y quita las filas duplicadas, siempre se ejecuta y actúa como un preámbulo del script: 

# dataset <- data.frame(bruto_vendido, TVE_Ponderado, sorteo, cantidad_despachada, Trimestre)
# dataset <- unique(dataset)
# 1. Cargar librerías
library(dplyr)
library(ggplot2)

# Evitar notación científica en etiquetas
options(scipen = 999)

df <- dataset
colnames(df) <- make.names(colnames(df))

# 1. Agrupación y Limpieza
df_clean <- df %>%
  mutate(
    Despacho = as.numeric(cantidad_despachada),
    Venta = as.numeric(cantidad_vendida),
    Incumplidos = as.numeric(Sorteos_Incumplidos),
    Total = as.numeric(Total_Sorteos)
  ) %>%
  group_by(Distribuidor = nombre_distribuidor) %>%
  summarise(
    # Calculamos la base semanal real
    Despacho_Semanal = sum(Despacho, na.rm=T) / max(Total, 1),
    Tasa_Incumplimiento = sum(Incumplidos, na.rm=T) / max(sum(Total, na.rm=T), 1),
    TVE_Actual = sum(Venta, na.rm=T) / max(sum(Despacho, na.rm=T), 1)
  ) %>%
  filter(Despacho_Semanal > 100) %>% # Filtramos distribuidores insignificantes
  ungroup()

# 2. Lógica de Reasignación
df_mod <- df_clean %>%
  mutate(
    # Regla de Recorte (Castigo)
    Factor_Recorte = case_when(
      Tasa_Incumplimiento > 0.20 ~ -0.20,
      Tasa_Incumplimiento > 0.05 ~ -0.10,
      TRUE ~ 0
    ),
    Billetes_Recortados = Despacho_Semanal * Factor_Recorte,
    
    # Regla de Premio (Flexibilidad: 60% venta, <10% falla)
    Es_Candidato_Premio = ifelse(TVE_Actual >= 0.60 & Tasa_Incumplimiento <= 0.10, 1, 0),
    Capacidad_Crecimiento = ifelse(Es_Candidato_Premio == 1, Despacho_Semanal * 0.20, 0)
  )

# Bolsa de billetes recuperados
bolsa_recuperada <- abs(sum(df_mod$Billetes_Recortados, na.rm = T))
capacidad_total_premio <- sum(df_mod$Capacidad_Crecimiento, na.rm = T)

# 3. Distribución de la Bolsa
df_final <- df_mod %>%
  mutate(
    Billetes_Premio = if(capacidad_total_premio > 0) {
      Capacidad_Crecimiento * (min(bolsa_recuperada, capacidad_total_premio) / capacidad_total_premio)
    } else { 0 },
    Ajuste_Final = Billetes_Recortados + Billetes_Premio,
    Impacto_Pct = Ajuste_Final / Despacho_Semanal
  ) %>%
  arrange(desc(abs(Ajuste_Final))) %>%
  head(12)

# 4. Visualización Final (Alineada a la izquierda)
library(stringr) # Asegúrate de tener esta librería para el recorte de texto

ggplot(df_final, aes(x = reorder(Distribuidor, Ajuste_Final), y = Ajuste_Final, fill = Ajuste_Final > 0)) +
  geom_col(alpha = 0.8, width = 0.8) +
  
  geom_text(aes(
    label = paste0(ifelse(Ajuste_Final > 0, "+", ""), 
                   scales::comma(round(Ajuste_Final, 0)), 
                   " (", scales::percent(Impacto_Pct, accuracy=1), ")"),
    hjust = ifelse(Ajuste_Final > 0, -0.1, 1.1)
  ), size = 3, fontface = "bold") +
  
  coord_flip() +
  scale_fill_manual(values = c("#E74C3C", "#27AE60")) +
  
  # OPCIONAL: Recorta los nombres de distribuidores a 25 caracteres para ganar espacio a la izquierda
  scale_x_discrete(labels = function(x) str_trunc(x, 25)) +
  
  scale_y_continuous(expand = expansion(mult = c(0.2, 0.2)), labels = scales::comma) +
  
  labs(x = NULL, y = "Diferencia de Billetes") +
  
  theme_minimal(base_size = 8) + 
  theme(
    legend.position = "none",
    axis.text.y = element_text(size = 8, face = "bold", hjust = 1), # Alinea texto de etiquetas a la derecha
    axis.title.x = element_text(size = 9),
    panel.grid.minor = element_blank(),
    # MARGENES: El segundo valor (10) es el derecho, el cuarto (0) es el izquierdo. 
    # Al poner 0 en el cuarto, pegamos el texto al borde izquierdo del visual.
    plot.margin = margin(t = 5, r = 10, b = 5, l = 0) 
  )