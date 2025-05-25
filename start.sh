
#!/bin/bash
echo "🚀 Ejecutando generación de dataset..."
python generar_dataset_ml.py

echo "✅ Dataset generado. Entrenando modelos..."
python entrenar_modelo_ml.py

echo "🎯 Proceso completo."
