import '../css/ImportTaskPanel.scss';
import React from 'react';
import PropTypes from 'prop-types';
import ErrorMessage from './ErrorMessage';

class ImportImagesFromUrlPanel extends React.Component {
  static defaultProps = {
  };

  static propTypes = {
      onImported: PropTypes.func.isRequired,
      onCancel: PropTypes.func,
      projectId: PropTypes.number.isRequired
  };

  constructor(props){
    super(props);

    this.state = {
      error: "",
      importingFromUrl: false,
      progress: 0,
      bytesSent: 0,
      importUrl: ""
    };
  }

  defaultTaskName = () => {
    return `Task of ${new Date().toISOString()}`;
  }

  cancel = (e) => {
    this.props.onCancel();
  }
  
  handleChangeImportUrl = (e) => {
    this.setState({importUrl: e.target.value});
  }

  handleConfirmImportUrl = () => {
    this.setState({importingFromUrl: true});

    $.post(`/api/projects/${this.props.projectId}/tasks/importimages`,
      {
        url: this.state.importUrl,
        name: this.defaultTaskName()
      }
    ).done(json => {
      this.setState({importingFromUrl: false});

      if (json.id){
        this.props.onImported();
      }else{
        this.setState({error: json.error || `Cannot import from URL, server responded: ${JSON.stringify(json)}`});
      }
    })
    .fail(() => {
        this.setState({importingFromUrl: false, error: "Cannot import from URL. Check your internet connection."});
    });
  }

  render() {
    return (
      <div className="import-task-panel theme-background-highlight">
        <div className="form-horizontal">
          <ErrorMessage bind={[this, 'error']} />

          <button type="button" className="close theme-color-primary" aria-label="Close" onClick={this.cancel}><span aria-hidden="true">&times;</span></button>
          <h4>Import Images From URL</h4>
          <p>You can import all images from the images galery. You must provide the url of the category itself.</p>          
          
          <div className="form-inline">
            <div className="form-group">
              <input disabled={this.state.importingFromUrl} onChange={this.handleChangeImportUrl} size="45" type="text" className="form-control" placeholder="http://" value={this.state.importUrl} />
              <button onClick={this.handleConfirmImportUrl}
                      disabled={this.state.importUrl.length < 4 || this.state.importingFromUrl} 
                      className="btn-import btn btn-primary"><i className="glyphicon glyphicon-cloud-download"></i> Import</button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default ImportImagesFromUrlPanel;
