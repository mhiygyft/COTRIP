# #!/usr/bin/env bash
# set -o errexit

# python -m pip install --upgrade pip
# pip install -r requirements.txt

# python manage.py collectstatic --noinput
# python manage.py migrate --noinput

# python manage.py seed_transport_data
# python manage.py seed_multicity_flights
# python manage.py seed_web_travel_content
# python manage.py seed_youth_homestays_hotspots
# python manage.py seed_real_image_urls
#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

python manage.py seed_transport_data
python manage.py seed_multicity_flights
python manage.py seed_web_travel_content
python manage.py seed_youth_homestays_hotspots
python manage.py seed_real_image_urls

python manage.py loaddata data.json || true