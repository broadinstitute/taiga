{% extends "base.tpl" %}
{% block title %}Home{% endblock %}
{% block content %}

  <h1>Taiga</h1>
  <p>Welcome to Taiga: a light-weight repository for capturing, versioning and accessing datasets.</p>
  <p>Click one of the options at the at the top to find a dataset or upload a new dataset.</p>

  <div class="row">
    <div class="col-md-6">
      <h2>Latest datasets</h2>

      {% for ds in latest_datasets %}
        <p>{{ ds.created_timestamp[:10] }} <a href="/dataset/show/{{ds.dataset_id}}">{{ ds.name }}</a></p>
      {% endfor %}
    </div>

    <div class="col-md-6">
      <h2>Changelog</h2>
      {{ changelog }}
    </div>
  </div>

{% endblock %}