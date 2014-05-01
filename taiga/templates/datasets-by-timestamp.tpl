{% extends "base.tpl" %}
{% block title %}Home{% endblock %}
{% block content %}
  <h2>Datasets ordered by timestamp</h2>

  <table class="table table-bordered table-striped">
    <thead>
      <tr>
          <th>Name</th>
          <th>Description</th>
          <th>Created Timestamp</th>
      </tr>
    </thead>
    
    <tbody>
      {% for ds in datasets %}
      <tr>
        <td><a href="/dataset/show/{{ds.dataset_id}}">{{ ds.name }}</a></td>
        <td>{{ ds.description }}</td>
        <td>{{ ds.created_timestamp }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

{% endblock %}