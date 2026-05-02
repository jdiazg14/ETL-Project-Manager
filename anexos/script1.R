# El código siguiente, que crea un dataframe y quita las filas duplicadas, siempre se ejecuta y actúa como un preámbulo del script: 

# dataset <- data.frame(bruto_vendido, TVE_Ponderado, sorteo, cantidad_despachada, Trimestre)
# dataset <- unique(dataset)
# 1. Cargar librerías
library(dplyr)

library(ggplot2)

library(ggrepel) # Para que los nombres de los departamentos no se amontonen



df <- dataset

colnames(df) <- make.names(colnames(df))



# 2. Limpieza de datos

df$bruto_vendido <- suppressWarnings(as.numeric(gsub(",", ".", as.character(df$bruto_vendido))))

df$TVE_Ponderado <- suppressWarnings(as.numeric(gsub(",", ".", as.character(df$TVE_Ponderado))))

df$anio <- suppressWarnings(as.numeric(as.character(df$anio)))

df$Trimestre <- suppressWarnings(as.numeric(as.character(df$Trimestre)))



df <- df %>% filter(!is.na(bruto_vendido) & !is.na(nombre_depto) & bruto_vendido > 0)



# Crear un índice de tiempo consecutivo (Ej. 2023 Q1 = 1, 2023 Q2 = 2...)

df <- df %>%

arrange(anio, Trimestre) %>%

mutate(Periodo_Tiempo = as.numeric(as.factor(paste(anio, Trimestre))))



# 3. CONSTRUCCIÓN DE MÉTRICAS Y PROYECCIÓN POR DEPARTAMENTO

dept_stats <- df %>%

group_by(Departamento = nombre_depto) %>%

summarise(

Ventas_Promedio = mean(bruto_vendido, na.rm = TRUE),

TVE_Promedio = mean(TVE_Ponderado, na.rm = TRUE),

# Proyección lineal: Calculamos la pendiente (crecimiento/decrecimiento por trimestre)

Crecimiento_Proyectado = ifelse(n() > 1, lm(bruto_vendido ~ Periodo_Tiempo)$coefficients[2], 0)

) %>%

filter(!is.na(Crecimiento_Proyectado))



# 4. MODELO DE CONGLOMERADOS (K-MEANS CLUSTERING)

# Estandarizamos los datos para que K-Means no se confunda con los millones vs porcentajes

if(nrow(dept_stats) >= 3) {

set.seed(123) # Para que los colores de los grupos sean estables

datos_modelo <- scale(dept_stats %>% select(Ventas_Promedio, Crecimiento_Proyectado))


# Creamos 3 grupos estratégicos

kmeans_result <- kmeans(datos_modelo, centers = 3, nstart = 25)

dept_stats$Cluster <- as.factor(kmeans_result$cluster)


# Convertir el Crecimiento Proyectado a Porcentaje relativo al promedio de ventas para lectura fácil

dept_stats$Crecimiento_Pct <- dept_stats$Crecimiento_Proyectado / dept_stats$Ventas_Promedio

} else {

dept_stats$Cluster <- as.factor(1)

dept_stats$Crecimiento_Pct <- 0

}



# 5. GRÁFICO ESTRATÉGICO (MATRIZ)

# Calculamos promedios globales para dibujar los ejes que dividen los cuadrantes

mediana_ventas <- median(dept_stats$Ventas_Promedio, na.rm = TRUE)

mediana_crecimiento <- 0 # El eje de crecimiento se divide en positivo (arriba) y negativo (abajo)



ggplot(dept_stats, aes(x = Ventas_Promedio, y = Crecimiento_Pct, color = Cluster)) +

# Líneas divisorias de cuadrantes

geom_hline(yintercept = mediana_crecimiento, linetype = "dashed", color = "gray50") +

geom_vline(xintercept = mediana_ventas, linetype = "dashed", color = "gray50") +


# Burbujas de los departamentos (el tamaño depende de su TVE)

geom_point(aes(size = TVE_Promedio), alpha = 0.8) +


# Nombres de los departamentos

geom_text_repel(aes(label = Departamento), size = 3, fontface = "bold", show.legend = FALSE) +


# Escalas y formatos

scale_y_continuous(labels = scales::percent) +

scale_size_continuous(range = c(3, 10), name = "TVE % (Eficiencia)") +

scale_color_manual(values = c("#3498DB", "#E67E22", "#9B59B6"), name = "Conglomerado") +


# Títulos estratégicos

labs(

# title = "MATRIZ DE PROYECCIÓN Y CONGLOMERADOS TERRITORIALES",

# subtitle = "Eje Y: Crecimiento Proyectado | Eje X: Volumen de Ventas | Tamaño: Eficiencia (TVE)",

x = "Volumen de Ventas Promedio",

y = "Crecimiento Proyectado (Tendencia Próx. Trimestre)"

) +


# Etiquetas de Cuadrantes (Anotaciones)

annotate("text", x = max(dept_stats$Ventas_Promedio)*0.9, y = max(dept_stats$Crecimiento_Pct)*0.9, label = "ESTRELLAS\n(Alta Venta, Alto Crecimiento)", color = "gray40", fontface = "italic", size = 3) +

annotate("text", x = min(dept_stats$Ventas_Promedio)*1.1, y = max(dept_stats$Crecimiento_Pct)*0.9, label = "INCÓGNITAS\n(Baja Venta, Alto Crecimiento)", color = "gray40", fontface = "italic", size = 3) +


theme_minimal(base_size = 11) +

theme(

plot.title = element_text(face = "bold", color = "#2C3E50"),

legend.position = "bottom"

)